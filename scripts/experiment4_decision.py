#!/usr/bin/env python3
"""Apply experiment 4's pre-registered decision rule: do the orderings survive?

Pre-registered at `docs/preregistration/pseudo-reality.md`, commit 367ee93, with
deviations D1-D7 appended there. This script implements that rule and nothing
else. The rule, verbatim:

> * **Robust** if the ordering has the **same sign in ≥ 9 of the 10 sampled
>   models** **and** **disjoint intervals in ≥ 7 of the 10**.
> * **Fragile** if the sign **flips in ≥ 3 of the 10**.
> * **Neither** — anything between — is reported as **"not established either
>   way"** with both counts given. It is not evidence of robustness and must not
>   be written as if it were.
> * **Both counts are reported for every comparison**, whichever branch fires,
>   including the reference model's value alongside so the reader can see whether
>   the sampled models straddle it.
> * **Flip attribution**: if any comparison is fragile, the flipping models' six
>   parameter values are tabulated next to the non-flipping ones. **No
>   regression, no significance test, no claim of a mechanism.**

    python scripts/experiment4_decision.py          the tables and the verdicts
    python scripts/experiment4_decision.py --json   the same, machine-readable

Runs no simulation.

WHAT THE SIGN IS COUNTED AGAINST. Not against zero in the abstract: against **the
reference model's own sign** (model 00, unperturbed). A "flip" is a sampled model
whose ordering runs the other way from the design point where the claim was
measured. Counting against zero would give the same answer whenever the reference
is non-zero, which it is everywhere here, but the reference is the right anchor
and stating it removes the ambiguity.

WHAT THIS EXPERIMENT CANNOT SAY, carried into every sentence that quotes it. The
family perturbs *implementation* choices — actuation noise, sensor dropout,
contact-solver effort, timestep — around the design point. The kinematics, the
traction model, the pursuer's lock-on law and the sensor geometry are identical in
every model. A result robust here is robust to how carefully the simulator is
integrated and how noisy its sensors are, **not** to whether the model is right.
This is not a reality-gap study: no hardware, no ARGoS, no second simulator, and
§12.3 already records that none of those exist.

PAIRING. Runs pair WITHIN a model by run index — the two sides of a comparison see
the same placements — and are NOT paired across models, because `dt` and
`collision_iterations` differ between models and the same seed does not produce
the same trajectory. Every count below is a count over models of a within-model
statistic.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from swarm_harness.load import Records, load_jsonl        # noqa: E402
from swarm_harness.stats import median_ci, wilson_ci      # noqa: E402

MODELS = list(range(0, 11))          # 00 is the unperturbed reference
SAMPLED = MODELS[1:]                 # the ten the rule counts over
SIGN_AGREE_ROBUST = 9                # >= 9 of 10 same sign
DISJOINT_ROBUST = 7                  # and >= 7 of 10 disjoint
FLIPS_FRAGILE = 3                    # >= 3 of 10 sign flips

CLASS_FLAT = ["S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3"]
SEARCHED_S3 = ["S3-survival_task-s1", "S3-survival_task-s2", "S3-survival_task-s3"]
RP = [0.1, 0.35, 1.0]
KAPPA = [0.0, 5.0]
ROUGH, FLAT = 0.9, 0.0

_CACHE: dict[str, Records] = {}

# ---- amendment D8: the corrected pursuit ------------------------------------
# `--fixed` re-reads the PURSUIT half of the five dt = 0.05 models from the
# sweeps re-run with the dt-aware p_lock, and everything else from the original
# files. That is not a convenience: the six dt = 0.10 models are bit-identical
# under the fix, which is proved by byte-diff in the run log rather than assumed,
# so re-running them would burn compute to reproduce files that already exist.
# Comparisons 1 and 2 are aggregation and contain no pursuer, so `--fixed` cannot
# and does not change them.
FIXED_DT05 = (2, 3, 4, 5, 10)
USE_FIXED = False


def rec(group: str, model: int) -> Records:
    fixed = USE_FIXED and group == "pursuit" and model in FIXED_DT05
    key = (f"pseudo_reality_pursuit_fixed_model_{model:02d}" if fixed
           else f"pseudo_reality_{group}_model_{model:02d}")
    if key not in _CACHE:
        _CACHE[key] = load_jsonl(REPO / "results" / f"{key}.jsonl")
    return _CACHE[key]


# ------------------------------------------------------------------ statistics
def hold_by_run(model: int, row: str) -> dict[int, float]:
    """Run index -> dispersion at θ_m = 0.9 over the SAME RUN's flat ground."""
    r = rec("aggregation", model)
    flat = {x["run_index"]: x["final_dispersion"]
            for x in r.filter(row=row, **{"terrain.friction_amplitude": FLAT}).rows}
    return {x["run_index"]: x["final_dispersion"] / flat[x["run_index"]]
            for x in r.filter(row=row, **{"terrain.friction_amplitude": ROUGH}).rows
            if x["run_index"] in flat and flat[x["run_index"]]}


def paired_diff(a: dict[int, float], b: dict[int, float]) -> dict:
    keys = sorted(set(a) & set(b))
    d = [a[k] - b[k] for k in keys]
    m, lo, hi = median_ci(d)
    return dict(value=m, lo=lo, hi=hi, n=len(keys),
                sign=int(np.sign(m)), disjoint=bool(lo > 0 or hi < 0))


def per_robot(rows) -> dict:
    """Mean per-robot survival with a Wilson interval (§12.1 D0)."""
    flags: list[float] = []
    for x in rows:
        n, s = int(x["n"]), int(x["survivors"])
        flags.extend([1.0] * s + [0.0] * (n - s))
    p, lo, hi = wilson_ci(flags)
    return dict(value=p, lo=lo, hi=hi, robots=len(flags), runs=len(rows))


def survival(model: int, row: str, rp=None, kappa=None) -> dict:
    kw = {"row": row}
    if rp is not None:
        kw["pursuer.range"] = rp
    if kappa is not None:
        kw["pursuer.confusion"] = kappa
    return per_robot(rec("pursuit", model).filter(**kw).rows)


def disjoint(a: dict, b: dict) -> bool:
    return a["lo"] > b["hi"] or b["lo"] > a["hi"]


def best_of(model: int, rows: list[str], key) -> str:
    """§21 branch (b): best-of-three per cell, never the seed-1 row alone."""
    return min(rows, key=lambda r: key(model, r))


# ---------------------------------------------------------------- comparisons
def comparison_1(model: int) -> dict:
    """Terrain tax: S2-gauci against best-of-three S2-class-flat, at θ_m = 0.9.

    Positive means the enumerated row is taxed MORE than the tuned one, which is
    the ordering the record states.
    """
    best = best_of(model, CLASS_FLAT,
                   lambda mm, r: float(np.median(list(hold_by_run(mm, r).values()))))
    out = paired_diff(hold_by_run(model, "S2-gauci"), hold_by_run(model, best))
    out["best_class_flat"] = best
    for row in ["S2-gauci"] + CLASS_FLAT:
        v = list(hold_by_run(model, row).values())
        m, lo, hi = median_ci(v)
        out.setdefault("holds", {})[row] = dict(value=m, lo=lo, hi=hi)
    return out


def comparison_2(model: int) -> dict:
    """Capability flatness: S4-terrain † minus S2-searched †, at θ_m = 0.9, n = 20.

    Positive means the terrain bit is WORSE, which is the ordering A1 states.
    n = 20 by D5: the only n at which A1 is graded SUPPORTED.
    """
    out = paired_diff(hold_by_run(model, "S4-terrain"), hold_by_run(model, "S2-searched"))
    for row in ("S2-searched", "S4-terrain"):
        m, lo, hi = median_ci(list(hold_by_run(model, row).values()))
        out.setdefault("holds", {})[row] = dict(value=m, lo=lo, hi=hi)
    return out


def comparison_3(model: int, row: str) -> dict:
    """κ-response ratio: survival at κ = 5 over κ = 0, at r_p = 0.35 m.

    The "sign" of a ratio is whether it exceeds 1 — confusion buys survival, or it
    does not — and "disjoint" is the two Wilson intervals not overlapping.
    """
    lo_k = survival(model, row, rp=0.35, kappa=KAPPA[0])
    hi_k = survival(model, row, rp=0.35, kappa=KAPPA[-1])
    ratio = hi_k["value"] / lo_k["value"] if lo_k["value"] else float("inf")
    return dict(value=ratio, sign=int(np.sign(ratio - 1.0)),
                disjoint=disjoint(lo_k, hi_k), kappa_lo=lo_k, kappa_hi=hi_k)


def _survival_gap(model: int, a: str, b: str, rp: float) -> dict:
    """Mean per-robot survival difference a − b at one r_p, pooled over κ."""
    sa, sb = survival(model, a, rp=rp), survival(model, b, rp=rp)
    return dict(value=sa["value"] - sb["value"],
                sign=int(np.sign(sa["value"] - sb["value"])),
                disjoint=disjoint(sa, sb), a=sa, b=sb)


def comparison_4(model: int, rp: float) -> dict:
    """Matched pair: B1-ternary ‡ minus D-dispersive ‡, pooled over κ ∈ {0, 5}."""
    return _survival_gap(model, "B1-ternary", "D-dispersive", rp)


def comparison_5(model: int, rp: float, reference: str) -> dict:
    """Best-of-three searched S = 3 † minus a reference row, pooled over κ.

    Best-of-three is PER CELL, per §21 branch (b), which experiment 1's 166% seed
    spread put firmly in force. Two references by D1: B0 is the capability claim
    that goes in the abstract, B1 the regime-specific one.
    """
    best = best_of(model, SEARCHED_S3, lambda mm, r: -survival(mm, r, rp=rp)["value"])
    out = _survival_gap(model, best, reference, rp)
    out["best_searched"] = best
    out["per_seed"] = {r: survival(model, r, rp=rp)["value"] for r in SEARCHED_S3}
    return out


# ------------------------------------------------------------------- the rule
def apply_rule(name: str, per_model: dict[int, dict], out: dict) -> dict:
    ref = per_model[0]
    same = [m for m in SAMPLED if per_model[m]["sign"] == ref["sign"]]
    flips = [m for m in SAMPLED if per_model[m]["sign"] != ref["sign"]]
    dj = [m for m in SAMPLED if per_model[m]["disjoint"]]

    if len(flips) >= FLIPS_FRAGILE:
        verdict = "FRAGILE"
    elif len(same) >= SIGN_AGREE_ROBUST and len(dj) >= DISJOINT_ROBUST:
        verdict = "ROBUST"
    else:
        verdict = "not established either way"

    print(f"\n  {name}")
    print(f"    reference (model 00): {ref['value']:+.4f}"
          + (f"  [{ref['lo']:+.4f}, {ref['hi']:+.4f}]" if "lo" in ref else "")
          + f"   sign {ref['sign']:+d}   {'disjoint' if ref['disjoint'] else 'overlapping'}")
    cells = []
    for m in SAMPLED:
        v = per_model[m]
        mark = "" if v["sign"] == ref["sign"] else "  FLIP"
        cells.append(f"{m:02d}:{v['value']:+.4f}{'*' if v['disjoint'] else ' '}{mark}")
    for i in range(0, len(cells), 3):
        print("      " + "   ".join(f"{c:<26s}" for c in cells[i:i + 3]))
    print(f"    same sign as reference {len(same)}/10 (rule: >= {SIGN_AGREE_ROBUST}); "
          f"disjoint {len(dj)}/10 (rule: >= {DISJOINT_ROBUST}); "
          f"flips {len(flips)}/10 (fragile at >= {FLIPS_FRAGILE})")
    print(f"    >>> {verdict}")

    # Best-of-three is chosen PER MODEL, so which row won is part of the result:
    # a selection that jumps between seeds from model to model is a weaker
    # ordering than one where the same row wins everywhere, and the reader
    # cannot see that from the counts alone. Per the Phase 2 review, the
    # per-seed values travel with every best-of-three number.
    for key, label in (("best_class_flat", "best S2-class-flat"),
                       ("best_searched", "best searched S = 3")):
        if key in ref:
            picks = [per_model[m][key].split("-")[-1] for m in MODELS]
            uniq = sorted(set(picks))
            print(f"    {label} per model (00 first): " + " ".join(picks)
                  + f"   [{len(uniq)} distinct: {', '.join(uniq)}]")
    if "per_seed" in ref:
        for seed in sorted(ref["per_seed"]):
            vals = " ".join(f"{per_model[m]['per_seed'][seed]:.3f}" for m in MODELS)
            print(f"      per seed {seed.split('-')[-1]}: {vals}")

    entry = dict(reference={k: v for k, v in ref.items() if k in
                            ("value", "lo", "hi", "sign", "disjoint")},
                 per_model={str(m): {k: v for k, v in per_model[m].items()
                                     if k in ("value", "lo", "hi", "sign", "disjoint")}
                            for m in SAMPLED},
                 same_sign=len(same), disjoint=len(dj), flips=len(flips),
                 flipping_models=flips, verdict=verdict)
    for key in ("best_class_flat", "best_searched"):
        if key in ref:
            entry[key] = {str(m): per_model[m][key] for m in MODELS}
    if "per_seed" in ref:
        entry["per_seed"] = {str(m): per_model[m]["per_seed"] for m in MODELS}
    out["orderings"][name] = entry
    return entry


def summarise(comparison: str, names: list[str], out: dict) -> None:
    """D7: a comparison is robust only if every ordering in it is."""
    vs = [out["orderings"][n]["verdict"] for n in names]
    if any(v == "FRAGILE" for v in vs):
        v = "FRAGILE"
    elif all(v == "ROBUST" for v in vs):
        v = "ROBUST"
    else:
        v = "not established either way"
    out["comparisons"][comparison] = dict(orderings=names, verdict=v,
                                          per_ordering=dict(zip(names, vs)))
    print(f"\n  ===> {comparison}: {v}"
          + ("" if len(names) == 1 else
             f"   (from {len(names)} orderings: "
             + ", ".join(f"{n.split(' — ')[-1]} {x}" for n, x in zip(names, vs)) + ")"))


def flip_table(out: dict) -> None:
    """Every flipping model's six parameters, next to the ones that did not flip.

    A LEAD FOR FUTURE WORK, NOT A FINDING. Ten models over six parameters cannot
    support a regression and none is fitted; the pre-registration forbids it in
    as many words, because fitting one would manufacture a mechanism the design
    cannot see.
    """
    flippers = sorted({m for e in out["orderings"].values() for m in e["flipping_models"]})
    if not flippers:
        print("\n  no ordering flipped in any sampled model — no flip table to draw")
        out["flip_table"] = None
        return
    sys.path.insert(0, str(REPO / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen", REPO / "scripts" / "build_pseudo_reality_configs.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    models = gen.sample()
    params = [p for p, *_ in gen.PARAMS]
    print(f"\n{'='*78}\nFLIP ATTRIBUTION — a lead, not a finding\n{'='*78}")
    print("  No regression, no significance test, no claim of a mechanism: ten models")
    print("  over six parameters cannot support one, and the pre-registration says so.\n")
    print("  " + f"{'model':7s}" + "".join(f"{p.split('.')[-1][:13]:>15s}" for p in params)
          + "   flipped")
    for i, m in enumerate(models, start=1):
        which = [n for n, e in out["orderings"].items() if i in e["flipping_models"]]
        print("  " + f"{i:02d}{'  *' if which else '   '}   "
              + "".join(f"{gen.fmt(p, m[p]):>15s}" for p in params)
              + f"   {len(which)}")
    out["flip_table"] = {f"{i:02d}": {p: models[i - 1][p] for p in params}
                         for i in range(1, 11)}
    out["flip_counts"] = {f"{i:02d}": len([n for n, e in out["orderings"].items()
                                           if i in e["flipping_models"]])
                          for i in range(1, 11)}


def reach_diagnostic(out: dict) -> None:
    """Does every model still aggregate at all? REPORTED, NOT THRESHOLDED.

    Written before any Phase 5 number was read, and deliberately not turned into
    a rule: the pre-registration fixed no reach contingency for this experiment
    and inventing one after the fact is exactly what a pre-registration is for
    preventing. But a hold ratio measured on a swarm that never aggregated is a
    measurement of the clock rather than of terrain — that is how §20's diagnosis
    went wrong and why experiment 2 carried a τ contingency — and several of these
    models drop up to 9% of neighbour sightings. So the reach of every row in
    every model is printed, and any comparison drawn from a model whose reach has
    collapsed must be read with that in front of it.
    """
    print(f"\n{'='*78}\nREACH DIAGNOSTIC — reported, NOT thresholded, and not part of the rule"
          f"\n{'='*78}")
    print("  fraction of runs that ever formed a single cluster, at θ_m = 0.9, τ = 600 s\n")
    rows = ["S2-gauci"] + CLASS_FLAT + ["S2-searched", "S4-terrain"]
    print("  model  " + "".join(f"{r.replace('S2-class-flat-', 'cf-'):>13s}" for r in rows))
    table = {}
    for m in MODELS:
        vals = []
        for row in rows:
            c = rec("aggregation", m).filter(
                row=row, **{"terrain.friction_amplitude": ROUGH})
            p_, _lo, _hi = wilson_ci([1.0 if x else 0.0
                                      for x in c.column("ever_single_cluster")])
            vals.append(p_)
        table[str(m)] = dict(zip(rows, vals))
        tag = " (ref)" if m == 0 else "      "
        print(f"  {m:02d}{tag} " + "".join(f"{v:13.2f}" for v in vals))
    lowest = min((v, m, r) for m, d in table.items() for r, v in d.items())
    print(f"\n  lowest reach anywhere: {lowest[0]:.2f} ({lowest[2]} in model {lowest[1]})")
    out["reach_diagnostic"] = table


def main() -> int:
    global USE_FIXED
    USE_FIXED = "--fixed" in sys.argv

    missing = [f"pseudo_reality_{g}_model_{m:02d}.jsonl"
               for m in MODELS for g in ("aggregation", "pursuit")
               if not (REPO / "results" / f"pseudo_reality_{g}_model_{m:02d}.jsonl").exists()]
    if USE_FIXED:
        missing += [f"pseudo_reality_pursuit_fixed_model_{m:02d}.jsonl" for m in FIXED_DT05
                    if not (REPO / "results"
                            / f"pseudo_reality_pursuit_fixed_model_{m:02d}.jsonl").exists()]
    if missing:
        print(f"missing {len(missing)} results files, first: {missing[0]}", file=sys.stderr)
        return 1

    out: dict = {"rule_source": "docs/preregistration/pseudo-reality.md @ 367ee93 (+D1-D8)",
                 "corrected_pursuit": bool(USE_FIXED),
                 "orderings": {}, "comparisons": {}}

    print("=" * 78)
    if USE_FIXED:
        print("AMENDMENT D8 RUN — the PURSUIT comparisons re-read from the sweeps re-run")
        print(f"with the dt-aware p_lock, for models {', '.join(f'{m:02d}' for m in FIXED_DT05)}"
              " (the dt = 0.05 ones).")
        print("This is NOT the pre-registered test. The registered rule fired on the")
        print("original family and that verdict stands in §25, unedited. Comparisons 1")
        print("and 2 are aggregation and are unchanged by construction.")
        print("=" * 78)
        print("=" * 78)
    print("EXPERIMENT 4 — pseudo-reality robustness.  11 models (00 = unperturbed")
    print("reference), 100 runs/cell, paired within a model and never across models.")
    print("Signs are counted against the REFERENCE model's sign. `*` marks a model")
    print("whose intervals are disjoint; FLIP marks one whose sign runs the other way.")
    print("=" * 78)

    reach_diagnostic(out)

    print(f"\n{'='*78}\nCOMPARISON 1 — terrain tax: S2-gauci vs best-of-three S2-class-flat\n{'='*78}")
    n1 = "C1 — hold-ratio difference at θ_m = 0.9"
    apply_rule(n1, {m: comparison_1(m) for m in MODELS}, out)
    summarise("comparison 1 (terrain tax)", [n1], out)

    print(f"\n{'='*78}\nCOMPARISON 2 — capability flatness: S4-terrain † vs S2-searched †\n{'='*78}")
    n2 = "C2 — hold-ratio difference at θ_m = 0.9, n = 20"
    apply_rule(n2, {m: comparison_2(m) for m in MODELS}, out)
    summarise("comparison 2 (capability flatness)", [n2], out)

    print(f"\n{'='*78}\nCOMPARISON 3 — κ-response ratio at r_p = 0.35 m, h = 1.93 s\n{'='*78}")
    names3 = []
    for row in ("B0-blind", "B1-ternary", "D-dispersive"):
        nm = f"C3 — κ-response ratio — {row}"
        names3.append(nm)
        apply_rule(nm, {m: comparison_3(m, row) for m in MODELS}, out)
    summarise("comparison 3 (confusion through aggregation)", names3, out)

    print(f"\n{'='*78}\nCOMPARISON 4 — B1-ternary ‡ vs D-dispersive ‡, pooled over κ\n{'='*78}")
    names4 = []
    for rp in RP:
        nm = f"C4 — B1 − D — r_p = {rp:g} m"
        names4.append(nm)
        apply_rule(nm, {m: comparison_4(m, rp) for m in MODELS}, out)
    summarise("comparison 4 (matched-pair ordering)", names4, out)

    print(f"\n{'='*78}\nCOMPARISON 5 — best-of-three searched S = 3 † vs B0 and vs B1\n{'='*78}")
    names5 = []
    for reference in ("B0-blind", "B1-ternary"):
        for rp in RP:
            nm = f"C5 — S3† − {reference} — r_p = {rp:g} m"
            names5.append(nm)
            apply_rule(nm, {m: comparison_5(m, rp, reference) for m in MODELS}, out)
    summarise("comparison 5 (searched S = 3 ordering)", names5, out)

    flip_table(out)

    print(f"\n{'='*78}\nVERDICTS — per comparison, never pooled across comparisons\n{'='*78}")
    for k, v in out["comparisons"].items():
        print(f"  {k:44s} {v['verdict']}")
    print("\n  \"not established either way\" is NOT evidence of robustness and must")
    print("  not be written as if it were. Both counts are printed above for every")
    print("  ordering, whichever branch fired.")

    if "--json" in sys.argv:
        print("\n" + json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
