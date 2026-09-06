#!/usr/bin/env python3
"""Phase A -- recompute the paper's hold ratios and survival intervals.

Reads only logged run files; runs no simulation.

A1  Hold ratios under ONE definition: the median of the per-run paired ratio,
    run index by run index against the same row's own flat-ground cell. The
    bootstrap interval is taken on the same quantity as the point estimate,
    which the retired ratio-of-medians could not do.

A2  Survival as the MEAN PER-ROBOT survival with a Wilson interval on the
    pooled robot count, replacing a bootstrap of the median run-level survival
    fraction. A survival fraction is a proportion of robots, and the median of a
    coarse per-run proportion lands on a grid value (0.00, 0.05, ...) whose
    bootstrap interval is an artefact of that grid.

Usage: python scripts/recompute_paired_and_survival.py [--json]
"""
from __future__ import annotations
import json, pathlib, sys
import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
from swarm_harness.load import load_jsonl                # noqa: E402
from swarm_harness.stats import median_ci, wilson_ci     # noqa: E402

_C: dict[str, object] = {}
def rec(p):
    if p not in _C:
        _C[p] = load_jsonl(REPO / "results" / f"{p}.jsonl")
    return _C[p]

OUT: dict[str, object] = {"sources": [], "A1_hold_ratios": {}, "A1_decomposition": {},
                          "A2_survival": {}, "A2_kappa": {}, "A2_pareto": {}}
def src(name):
    if name not in OUT["sources"]:
        OUT["sources"].append(name)

def paired_ratio(num_rows, den_rows, key="final_dispersion"):
    den = {x["run_index"]: x[key] for x in den_rows}
    xs = [x[key] / den[x["run_index"]] for x in num_rows
          if x["run_index"] in den and den[x["run_index"]]]
    m, lo, hi = median_ci(xs)
    return dict(value=round(m, 4), lo=round(lo, 4), hi=round(hi, 4), n=len(xs))

def per_robot(rows):
    """Mean per-robot survival with a Wilson interval on the pooled robot count."""
    flags = []
    for x in rows:
        n = int(x["n"]); s = int(x["survivors"])
        flags.extend([1.0] * s + [0.0] * (n - s))
    p, lo, hi = wilson_ci(flags)
    return dict(value=round(p, 4), lo=round(lo, 4), hi=round(hi, 4), robots=len(flags), runs=len(rows))

# ------------------------------------------------------------------ A1 -----
def hold(file, row, amp=0.9, **extra):
    src(f"results/{file}.jsonl")
    n = rec(file).filter(row=row, **{"terrain.friction_amplitude": amp}, **extra).rows
    d = rec(file).filter(row=row, **{"terrain.friction_amplitude": 0.0}, **extra).rows
    return paired_ratio(n, d)

for row in ("S2-gauci", "S2-flat", "S2-rough"):
    OUT["A1_hold_ratios"][f"tuning_control/{row}"] = hold("terrain_tuning_control", row)
    OUT["A1_hold_ratios"][f"tuning_control_r15/{row}"] = hold("terrain_tuning_control_r15", row)
for row in ("S2-gauci", "S2-searched", "S4-terrain"):
    OUT["A1_hold_ratios"][f"h3_capability/{row}"] = hold(
        "terrain_h3_capability", row, **{"terrain.correlation_length": 0.1})
OUT["A1_hold_ratios"]["mechanism/per-wheel@lambda0.1"] = hold(
    "terrain_mechanism", "per-wheel", **{"terrain.correlation_length": 0.1})
OUT["A1_hold_ratios"]["mechanism/scalar-centre@lambda0.1"] = hold(
    "terrain_mechanism", "scalar-centre", **{"terrain.correlation_length": 0.1})
for row in ("S2-gauci", "S2-rough"):
    OUT["A1_hold_ratios"][f"lambda_sweep/{row}@peak7.46cm"] = hold(
        "terrain_lambda_sweep", row, **{"terrain.correlation_length": 0.0746})

def decomposition(file):
    """Objective-tuning and terrain-tuning shares of the anchor-to-rough gap.

    NOT a hold ratio, and deliberately NOT paired-ratio'd. A decomposition needs
    two shares that add to the whole, which requires additive level estimates:
    median(gauci) - median(flat) + median(flat) - median(rough) is exactly
    median(gauci) - median(rough), and no per-run ratio has that property.
    Per-run ratios are also ill-conditioned here: the per-run gap is NEGATIVE in
    11 of 100 runs at 0.74 m and 31 of 100 at 1.5 m, so a median of per-run
    shares is an artefact of sign changes in the denominator.

    What the paired data does add is a significance test on the terrain term,
    reported alongside: the per-run difference D(flat) - D(rough), which is the
    quantity the terrain share is made of.
    """
    src(f"results/{file}.jsonl")
    d = {r: {x["run_index"]: x["final_dispersion"]
             for x in rec(file).filter(row=r, **{"terrain.friction_amplitude": 0.9}).rows}
         for r in ("S2-gauci", "S2-flat", "S2-rough")}
    keys = sorted(set(d["S2-gauci"]) & set(d["S2-flat"]) & set(d["S2-rough"]))
    lev = {r: float(np.median([d[r][k] for k in keys])) for r in d}
    gap = lev["S2-gauci"] - lev["S2-rough"]
    ter_paired = [d["S2-flat"][k] - d["S2-rough"][k] for k in keys]
    gap_paired = [d["S2-gauci"][k] - d["S2-rough"][k] for k in keys]
    mt, tlo, thi = median_ci(ter_paired)
    return dict(
        levels={r: round(v, 4) for r, v in lev.items()},
        objective_pct=round(100 * (lev["S2-gauci"] - lev["S2-flat"]) / gap, 1),
        terrain_pct=round(100 * (lev["S2-flat"] - lev["S2-rough"]) / gap, 1),
        terrain_term_paired=dict(value=round(mt, 4), lo=round(tlo, 4), hi=round(thi, 4),
                                 excludes_zero=bool(tlo > 0 or thi < 0)),
        per_run_gap_negative=int(sum(1 for g in gap_paired if g < 0)),
        runs=len(keys))

OUT["A1_decomposition"]["0.74m"] = decomposition("terrain_tuning_control")
OUT["A1_decomposition"]["1.5m"] = decomposition("terrain_tuning_control_r15")

# flat-ground reversal, paired
src("results/terrain_tuning_control.jsonl")
_f = {x["run_index"]: x["final_dispersion"]
      for x in rec("terrain_tuning_control").filter(row="S2-flat", **{"terrain.friction_amplitude": 0.0}).rows}
_g = {x["run_index"]: x["final_dispersion"]
      for x in rec("terrain_tuning_control").filter(row="S2-rough", **{"terrain.friction_amplitude": 0.0}).rows}
_k = sorted(set(_f) & set(_g))
_m, _lo, _hi = median_ci([(_g[k] - _f[k]) / _f[k] for k in _k])
OUT["A1_decomposition"]["flat_ground_reversal_pct"] = dict(
    value=round(100*_m, 1), lo=round(100*_lo, 1), hi=round(100*_hi, 1), n=len(_k),
    meaning="S2-rough costs this much against S2-flat on flat ground, paired per run")

# ------------------------------------------------------------------ A2 -----
src("results/pursuer_dispersive.jsonl")
for rp in (0.10, 0.20, 0.35, 0.60, 1.00):
    for row in ("B0-blind", "B1-ternary", "D-dispersive"):
        r = rec("pursuer_dispersive").filter(row=row, **{"pursuer.range": rp, "pursuer.handling_time": 1.93}).rows
        if r:
            OUT["A2_survival"][f"dispersive/h1.93/rp{rp}/{row}"] = per_robot(r)

src("results/pursuer_idea_b.jsonl")
for row in ("B0-blind", "B1-ternary", "B2-ternary-side", "B3-ternary-memory"):
    OUT["A2_survival"][f"idea_b/grid/{row}"] = per_robot(rec("pursuer_idea_b").filter(row=row).rows)

for h in (0.39, 1.93):
    for row in ("B0-blind", "B1-ternary", "D-dispersive"):
        r = rec("pursuer_dispersive").filter(row=row, **{"pursuer.handling_time": h})
        ks = sorted({x["pursuer.confusion"] for x in r.rows})
        lo = per_robot(r.filter(**{"pursuer.confusion": ks[0]}).rows)
        hi = per_robot(r.filter(**{"pursuer.confusion": ks[-1]}).rows)
        OUT["A2_kappa"][f"h{h}/{row}"] = dict(
            kappa_lo=lo, kappa_hi=hi, multiplier=round(hi["value"] / lo["value"], 2)
            if lo["value"] else None,
            intervals_overlap=not (hi["lo"] > lo["hi"] or lo["lo"] > hi["hi"]))

src("results/pursuer_pareto.jsonl")
for rp, k in ((0.2, 0.0), (0.35, 3.0), (1.0, 3.0)):
    for row in sorted({x["row"] for x in rec("pursuer_pareto").rows}):
        r = [x for x in rec("pursuer_pareto").rows
             if x["row"] == row and x["pursuer.range"] == rp and x["pursuer.confusion"] == k]
        if not r: continue
        surv = per_robot(r)
        keep = [x["final_dispersion"] for x in r if x["survivors"] >= 3]
        dm, dlo, dhi = median_ci(keep) if len(keep) >= 3 else (float("nan"),)*3
        OUT["A2_pareto"][f"rp{rp}/kappa{k}/{row}"] = dict(
            survival=surv,
            dispersion=None if not keep else dict(value=round(dm, 3), lo=round(dlo, 3),
                                                  hi=round(dhi, 3), runs_kept=len(keep)))

# ordering changes at the Pareto cell that S12 rests on
_cell = {k.split("/")[-1]: v for k, v in OUT["A2_pareto"].items() if k.startswith("rp0.35/kappa3.0")}
_d = _cell["D-dispersive"]["survival"]
OUT["A2_pareto"]["_S12_check"] = {
    row: dict(beats_D_on_survival=v["survival"]["lo"] > _d["hi"],
              survival=v["survival"]["value"], D=_d["value"])
    for row, v in _cell.items() if row != "D-dispersive"}

if __name__ == "__main__":
    print(json.dumps(OUT, indent=1))
