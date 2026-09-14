#!/usr/bin/env python3
"""Phase 0.2 -- recompute paper-source.md section 13 from the logged run files.

Reads only `results/*.jsonl` and `results/search_*.json`; runs no simulation.
Statistics come from `swarm_harness.stats` (the repository's own helpers) except
the two-sample ratio of medians, which the repository implements nowhere and
which is reproduced here under `rom()` with bootstrap_ci's conventions.

Usage: python scripts/verify_numbers.py [--json]
"""
from __future__ import annotations
import json, pathlib, sys
import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
from swarm_harness.load import load_jsonl                      # noqa: E402
from swarm_harness.stats import median_ci, wilson_ci           # noqa: E402

_C: dict[str, object] = {}
def rec(p):
    if p not in _C:
        _C[p] = load_jsonl(REPO / "results" / f"{p}.jsonl")
    return _C[p]
def srch(p):
    return json.loads((REPO / "results" / f"{p}.json").read_text())

RESULTS: list[dict] = []
def item(nid, claimed, sources):
    def deco(fn):
        try:
            got, note = fn()
            RESULTS.append(dict(id=nid, claimed=claimed, recomputed=got, note=note,
                                sources=sources))
        except Exception as e:  # a failure is a finding, not a crash
            RESULTS.append(dict(id=nid, claimed=claimed, recomputed="ERROR",
                                note=f"{type(e).__name__}: {e}", sources=sources))
        return fn
    return deco

def fm(v):
    m, lo, hi = median_ci(v); return f"{m:.4g} [{lo:.4g}, {hi:.4g}]"
def fw(flags):
    p, lo, hi = wilson_ci([1.0 if x else 0.0 for x in flags]); return f"{p:.3g} [{lo:.3g}, {hi:.3g}]"
def rom(num, den, seed=0, resamples=10_000):
    """Ratio of medians, independent-resample percentile bootstrap."""
    a, b = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    s = (np.median(a[rng.integers(0, a.size, (resamples, a.size))], axis=1)
         / np.median(b[rng.integers(0, b.size, (resamples, b.size))], axis=1))
    lo, hi = np.quantile(s, [0.025, 0.975])
    return float(np.median(a) / np.median(b)), float(lo), float(hi)
def frm(n, d):
    m, lo, hi = rom(n, d); return f"{m:.4g} [{lo:.4g}, {hi:.4g}]"
def paired(num, den, key="final_dispersion"):
    dn = {x["run_index"]: x[key] for x in den}
    return [x[key] / dn[x["run_index"]] for x in num if x["run_index"] in dn and dn[x["run_index"]]]
def cells(file, **kw):
    return rec(file).filter(**kw)

# --------------------------------------------------------------- validation
@item(9, "93 %", "gauci_scaling, small_n_* probes")
def _():
    probes = {k: rec(k).filter(n=2) for k in
              ("gauci_scaling", "small_n_noise_probe", "small_n_start_radius_probe", "small_n_time_gate")}
    s = {k: float(np.mean([1.0 if x else 0.0 for x in v.column("ever_single_cluster")]))
         for k, v in probes.items()}
    return (f"{100*s['gauci_scaling']:.0f} % (gauci_scaling, the canonical n=2 cell)",
            "other probes: " + ", ".join(f"{k} {100*x:.1f}%" for k, x in s.items() if k != "gauci_scaling"))
@item(10, "~10 %", "gauci_scaling n=2")
def _():
    g = rec("gauci_scaling").filter(n=2)
    still = float(np.mean([1.0 if x else 0.0 for x in g.column("single_cluster")]))
    share = float(np.median(g.column("fraction_time_single_cluster")))
    return f"{100*still:.0f} % still one cluster at tau", f"share of time single cluster is {100*share:.0f} %"
@item(11, "0.88 / 0.98 / 1.00", "gauci_scaling")
def _():
    v = {k[0]: float(np.mean([1.0 if x else 0.0 for x in rr.column("ever_single_cluster")]))
         for k, rr in rec("gauci_scaling").group_by(["n"]).items()}
    ten = [x for k, x in v.items() if k >= 10]
    return f"{v[2]:.2f} / {v[5]:.2f} / {min(ten):.2f}", f"n grid {sorted(v)}"
@item(12, "1.43", "gauci_scaling n=20")
def _():
    r = rec("gauci_scaling").filter(n=20); return fm(r.column("final_dispersion")), f"n={len(r)}"
@item(13, "1.3875 at every value, spread exactly 0", "link_distance")
def _():
    ld = rec("link_distance"); k = [f for f in ld.fields() if "link" in f.lower()]
    ds = [float(np.median(rr.column("final_dispersion"))) for _, rr in sorted(ld.group_by(k).items())]
    return (f"{min(ds):.4f} at every value, spread {max(ds)-min(ds):.4f}",
            f"{len(ds)} values of {k[0]}; max {max(ds):.4f}")
@item(14, "0.475 -> 0.967", "link_distance")
def _():
    # Three decimals, not two: §13 quotes this to three and a two-decimal
    # recomputation reads as a mismatch to check_section13's precision rule.
    ld = rec("link_distance"); k = [f for f in ld.fields() if "link" in f.lower()]
    fs = [float(np.median(rr.column("fraction_time_single_cluster"))) for _, rr in sorted(ld.group_by(k).items())]
    return f"{min(fs):.3f} -> {max(fs):.3f}", f"{len(fs)} values"
@item(18, "0 of 23", "terrain_h1_fine")
def _():
    g = sorted(rec("terrain_h1_fine").group_by(["terrain.slope_angle", "terrain.friction_amplitude"]).items())
    st = {k: median_ci(rr.column("final_dispersion")) for k, rr in g}
    base = st[(0.0, 0.0)]
    dj = [k for k, (m, lo, hi) in st.items() if k != (0.0, 0.0) and (hi < base[1] or lo > base[2])]
    return f"{len(dj)} of {len(st)-1}", f"baseline {base[0]:.4g} [{base[1]:.4g}, {base[2]:.4g}], 200 runs/cell"
@item(19, "1.385-1.430", "terrain_h1_fine")
def _():
    ms = [float(np.median(rr.column("final_dispersion")))
          for _, rr in rec("terrain_h1_fine").group_by(["terrain.slope_angle", "terrain.friction_amplitude"]).items()]
    return f"{min(ms):.4f}-{max(ms):.4f}", f"{len(ms)} cells"
@item(20, "0.89", "occlusion_shakedown")
def _():
    occ = rec("occlusion_shakedown"); ck = [f for f in occ.fields() if "correlation" in f][0]
    c = occ.filter(row="M0-gauci", **{"occlusion.fn_rate": 0.6, ck: 0.9})
    v = c.column("realised_fn_rate")
    return f"mean {np.mean(v):.4f}, median {np.median(v):.4f}", "the published 0.89 is the MEDIAN; the text calls it the mean"
@item(21, "4.68 vs 3.32", "occlusion_shakedown")
def _():
    occ = rec("occlusion_shakedown"); ck = [f for f in occ.fields() if "correlation" in f][0]
    band = lambda rr: [x["final_dispersion"] for x in rr.rows if 0.85 <= x["realised_fn_rate"] <= 0.95]
    co = band(occ.filter(row="M0-gauci", **{ck: 0.9})); ii = band(occ.filter(row="M0-gauci", **{ck: 0.0}))
    return f"{np.median(co):.2f} vs {np.median(ii):.2f}", f"n={len(co)} vs {len(ii)}"

# ------------------------------------------------------------------ H2 (s4)
def _h2_peaks(amp):
    h = rec("terrain_h2_powered_valid"); out = {}
    for row in sorted({x["row"] for x in h.rows}):
        r0 = float(np.median([x["state0_turn_radius"] for x in h.filter(row=row).rows]))
        best = None
        for L in sorted({x["terrain.correlation_length"] for x in h.rows}):
            n = h.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": amp}).column("final_dispersion")
            d = h.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.0}).column("final_dispersion")
            if not n or not d: continue
            v = float(np.median(n) / np.median(d))
            if best is None or v > best[1]: best = (L, v)
        out[row] = (best[0], best[1], r0, best[0] / r0)
    return out
@item(22, "0.69 for four of five rows", "terrain_h2_powered_valid, theta_m = 0.7")
def _():
    p = _h2_peaks(0.7)
    at = sum(1 for v in p.values() if abs(v[3] - 0.69) < 0.02)
    return f"{at} of {len(p)} at lambda/R0 = 0.69", "; ".join(f"{k} {v[3]:.2f}" for k, v in p.items()) + " -- the amplitude is not stated in the numbers table; at theta_m = 1.0 only 2 of 5"
@item(23, "44 %", "terrain_h2_powered_valid, theta_m = 1.0")
def _():
    # Peaks listed in §13's order -- half the axle, base, twice the axle -- so
    # the row reads as a sequence rather than needing the reader to reorder it.
    p = _h2_peaks(1.0); v = [p[k][1] for k in ("axle-half-R0-same", "base", "axle-x2-R0-same")]
    return f"{100*(max(v)-min(v))/min(v):.0f} %", "peaks " + " / ".join(f"{x:.2f}" for x in v)
@item(24, "648 %", "terrain_h2_powered_valid, theta_m = 1.0")
def _():
    p = _h2_peaks(1.0); v = [p[k][1] for k in ("R0-half-axle-same", "base", "R0-x2-axle-same")]
    return f"{100*(max(v)-min(v))/min(v):.0f} %", "peaks " + " / ".join(f"{x:.2f}" for x in v)

# ------------------------------------------------------------- mechanism, H3
def _mech(row):
    mech = rec("terrain_mechanism"); rr = mech.filter(row=row); flat = {}
    for x in rr.rows:
        if x["terrain.friction_amplitude"] == 0.0:
            flat.setdefault((x["run_index"], x["terrain.correlation_length"]), []).append(x["final_dispersion"])
    return [x["final_dispersion"] / float(np.median(flat[(x["run_index"], x["terrain.correlation_length"])]))
            for x in rr.rows if x["terrain.friction_amplitude"] != 0.0
            and (x["run_index"], x["terrain.correlation_length"]) in flat]
@item(25, "1.175 [1.154, 1.190]", "terrain_mechanism")
def _(): return fm(_mech("per-wheel")), "paired, pooled; re-seeded bootstrap (paper-source 12.1 records this)"
@item(26, "0.980 [0.976, 0.986]", "terrain_mechanism")
def _(): return fm(_mech("scalar-centre")), "paired, pooled; re-seeded bootstrap"
@item(27, "2.21 [1.90, 2.41]", "terrain_mechanism, lambda = 0.1")
def _():
    n = cells("terrain_mechanism", row="per-wheel", **{"terrain.correlation_length": 0.1, "terrain.friction_amplitude": 0.9})
    d = cells("terrain_mechanism", row="per-wheel", **{"terrain.correlation_length": 0.1, "terrain.friction_amplitude": 0.0})
    return frm(n.column("final_dispersion"), d.column("final_dispersion")), f"ratio of medians; paired form is {fm(paired(n.rows, d.rows))}"
for _nid, _row, _claim in ((28, "S2-gauci", "2.21 [1.90, 2.41]"), (29, "S2-searched", "1.10 [1.08, 1.15]"),
                           (30, "S4-terrain", "1.22 [1.16, 1.26]")):
    @item(_nid, _claim, "terrain_h3_capability, lambda = 0.1")
    def _(row=_row):
        n = cells("terrain_h3_capability", row=row, **{"terrain.correlation_length": 0.1, "terrain.friction_amplitude": 0.9})
        d = cells("terrain_h3_capability", row=row, **{"terrain.correlation_length": 0.1, "terrain.friction_amplitude": 0.0})
        return frm(n.column("final_dispersion"), d.column("final_dispersion")), f"paired form {fm(paired(n.rows, d.rows))}"
@item(31, "0.86 [0.79, 0.93]", "terrain_h3_capability")
def _():
    c = cells("terrain_h3_capability", row="S2-gauci", **{"terrain.correlation_length": 0.1, "terrain.friction_amplitude": 0.9})
    return fw(c.column("ever_single_cluster")), f"n={len(c)}"

# ------------------------------------------------------------------- pursuer
for _nid, _row, _claim in ((34, "B0-blind", "0.350"), (35, "B1-ternary", "0.650"),
                           (36, "B2-ternary-side", "0.450"), (37, "B3-ternary-memory", "0.700")):
    @item(_nid, _claim, "pursuer_idea_b (first sweep, h = 5.0 s)")
    def _(row=_row):
        r = cells("pursuer_idea_b", row=row)
        return fm(r.column("survival_fraction")), f"median over the whole grid, n={len(r)}"
@item(38, "8.8 / 29 %", "pursuer_idea_b, pursuer_dispersive")
def _():
    f = lambda p: 100 * float(np.mean([1.0 if x["survivors"] == 0 else 0.0 for x in rec(p).rows]))
    return f"{f('pursuer_idea_b'):.1f} / {f('pursuer_dispersive'):.1f} %", ""
def _kappa(row, h):
    r = cells("pursuer_dispersive", row=row, **{"pursuer.handling_time": h})
    ks = sorted({x["pursuer.confusion"] for x in r.rows})
    lo = float(np.mean(r.filter(**{"pursuer.confusion": ks[0]}).column("survival_fraction")))
    hi = float(np.mean(r.filter(**{"pursuer.confusion": ks[-1]}).column("survival_fraction")))
    return lo, hi
for _nid, _row, _claim in ((42, "B0-blind", "x3.05"), (43, "B0-blind", "x4.10")):
    pass
@item(42, "x3.05 (0.180 -> 0.548)", "pursuer_dispersive h=0.39")
def _():
    lo, hi = _kappa("B0-blind", 0.39); return f"x{hi/lo:.2f} ({lo:.3f} -> {hi:.3f})", "mean survival fraction"
@item(43, "x4.10 (0.144 -> 0.592)", "pursuer_dispersive h=1.93")
def _():
    lo, hi = _kappa("B0-blind", 1.93); return f"x{hi/lo:.2f} ({lo:.3f} -> {hi:.3f})", "mean survival fraction"
@item(44, "x2.23 / x1.91", "pursuer_dispersive")
def _():
    a = _kappa("B1-ternary", 0.39); b = _kappa("B1-ternary", 1.93)
    return f"x{a[1]/a[0]:.2f} / x{b[1]/b[0]:.2f}", f"({a[0]:.3f}->{a[1]:.3f} / {b[0]:.3f}->{b[1]:.3f})"
@item(45, "x1.20 / x1.13", "pursuer_dispersive")
def _():
    a = _kappa("D-dispersive", 0.39); b = _kappa("D-dispersive", 1.93)
    return f"x{a[1]/a[0]:.2f} / x{b[1]/b[0]:.2f}", f"({a[0]:.3f}->{a[1]:.3f} / {b[0]:.3f}->{b[1]:.3f})"
@item(46, "0.00 / 0.55 / 0.65", "pursuer_dispersive r_p=0.35 h=1.93")
def _():
    out = [fm(cells("pursuer_dispersive", row=r, **{"pursuer.range": 0.35, "pursuer.handling_time": 1.93}).column("survival_fraction"))
           for r in ("B0-blind", "B1-ternary", "D-dispersive")]
    return " / ".join(out), "pooled over kappa"
@item(48, "46.6 s (n = 94)", "pursuer_dispersive")
def _():
    r = cells("pursuer_dispersive", row="B0-blind", **{"pursuer.range": 0.35, "pursuer.handling_time": 1.93, "pursuer.confusion": 0.0})
    w = [x["time_to_wipeout"] for x in r.rows if x["time_to_wipeout"] is not None]
    return f"{np.median(w):.1f} s (n = {len(w)})", f"cell n={len(r)}"
@item(65, "379.9 / 386.3 / 504.8", "pursuer_pareto")
def _():
    out = []
    for rp, k in ((0.2, 0.0), (0.35, 3.0), (1.0, 3.0)):
        v = [x["final_dispersion"] for x in rec("pursuer_pareto").rows
             if x["row"] == "D-dispersive" and x["pursuer.range"] == rp and x["pursuer.confusion"] == k and x["survivors"] >= 3]
        out.append(fm(v))
    return " / ".join(out), "the three Pareto cells"
@item(66, "1.43-1.63", "pursuer_pareto")
def _():
    vals = []
    for row in ("B0-blind", "B1-ternary", "B2-ternary-side", "B3-ternary-memory"):
        for rp, k in ((0.2, 0.0), (0.35, 3.0)):
            v = [x["final_dispersion"] for x in rec("pursuer_pareto").rows
                 if x["row"] == row and x["pursuer.range"] == rp and x["pursuer.confusion"] == k and x["survivors"] >= 3]
            if len(v) >= 10: vals.append(float(np.median(v)))
    return f"{min(vals):.3f}-{max(vals):.3f}", "the two non-degenerate cells only"
@item(67, "0.80-0.85 vs 0.65", "pursuer_pareto")
def _():
    o = {row: float(np.median([x["survival_fraction"] for x in rec("pursuer_pareto").rows
         if x["row"] == row and x["pursuer.range"] == 0.35 and x["pursuer.confusion"] == 3.0]))
         for row in sorted({x["row"] for x in rec("pursuer_pareto").rows})}
    agg = [v for k, v in o.items() if k != "D-dispersive"]
    return f"{min(agg):.2f}-{max(agg):.2f} vs {o['D-dispersive']:.2f}", ""

# ----------------------------------------------------------- sections 9, 10
for _nid, _row, _amp, _claim in ((49, "S2-gauci", 0.0, "1.427"), (50, "S2-searched", 0.0, "1.253"),
                                 (51, "S2-gauci", 0.9, "3.150"), (52, "S2-searched", 0.9, "1.383"),
                                 (53, "S4-composite", 0.9, "1.999")):
    @item(_nid, _claim, "terrain_retune_cost")
    def _(row=_row, amp=_amp):
        return fm(cells("terrain_retune_cost", row=row, **{"terrain.friction_amplitude": amp}).column("final_dispersion")), ""
@item(54, "12.2 %", "terrain_retune_cost")
def _():
    a = float(np.median(cells("terrain_retune_cost", row="S2-gauci", **{"terrain.friction_amplitude": 0.0}).column("final_dispersion")))
    b = float(np.median(cells("terrain_retune_cost", row="S2-searched", **{"terrain.friction_amplitude": 0.0}).column("final_dispersion")))
    return f"{100*(a-b)/a:.1f} %", f"{a:.4f} -> {b:.4f}"
@item(55, "1.412 [1.349, 1.503]", "terrain_warm_s4")
def _(): return fm(cells("terrain_warm_s4", **{"terrain.friction_amplitude": 0.9}).column("final_dispersion")), ""
@item(56, "1.2595", "search_s4_warm.json")
def _(): return f"{srch('search_s4_warm')['best_training_objective']:.4f}", ""
@item(57, "1.3012 / 1.3009", "search_s4.json, search_s2.json")
def _(): return f"{srch('search_s4')['best_training_objective']:.4f} / {srch('search_s2')['best_training_objective']:.4f}", ""
@item(58, "0.464 (halves <= 0.254)", "search_s4_warm.json")
def _():
    s = srch("search_s4_warm"); b = np.array(s["best_constants"]); i = np.array(s["initial_mean"])
    return f"{np.linalg.norm(b-i):.3f} (halves {np.max(np.abs(b[:4]-b[4:])):.3f})", ""
@item(32, "600 x 12 = 7 200", "search_s2.json")
def _():
    s = srch("search_s2"); return f"{s['budget_evaluations']} x {s['runs_per_evaluation']} = {s['simulation_runs']}", f"training seed base {s['training_seed_base']}"

# --------------------------------------------------------- sections 13, 14
def _tune(file, row, amp):
    return cells(file, row=row, **{"terrain.friction_amplitude": amp})
# Rows 71 and 72 were CROSSED between this script and §13 until freeze lift 1:
# §13 row 71 is the paired form and row 72 the retired ratio-of-medians, and this
# script computed them the other way round. Both numbers were always right and
# both always reproduced; only the labels were swapped, so the fix is to the
# script, not to §13. (Phase 0 verification report, D-crossed-ids.)
@item(71, "2.149 / 1.200 / 1.099", "terrain_tuning_control")
def _():
    return " / ".join(fm(paired(_tune("terrain_tuning_control", r, 0.9).rows,
                                _tune("terrain_tuning_control", r, 0.0).rows))
                      for r in ("S2-gauci", "S2-flat", "S2-rough")), "median of paired ratios (§12.1 D1)"
@item(72, "2.208 / 1.195 / 1.104", "terrain_tuning_control")
def _():
    return " / ".join(frm(_tune("terrain_tuning_control", r, 0.9).column("final_dispersion"),
                          _tune("terrain_tuning_control", r, 0.0).column("final_dispersion"))
                      for r in ("S2-gauci", "S2-flat", "S2-rough")), "ratio of medians -- RETIRED by §12.1 D1"
def _dec(file):
    d = {r: float(np.median(_tune(file, r, 0.9).column("final_dispersion"))) for r in ("S2-gauci", "S2-flat", "S2-rough")}
    gap = d["S2-gauci"] - d["S2-rough"]
    return 100*(d["S2-gauci"]-d["S2-flat"])/gap, 100*(d["S2-flat"]-d["S2-rough"])/gap, d
@item(68, "96.9 % (99.7 at 1.5 m)", "terrain_tuning_control(_r15)")
def _():
    a, _, d = _dec("terrain_tuning_control"); b, _, _ = _dec("terrain_tuning_control_r15")
    return f"{a:.1f} % ({b:.1f} at 1.5 m)", f"dispersions {d['S2-gauci']:.4f}/{d['S2-flat']:.4f}/{d['S2-rough']:.4f}"
@item(69, "3.1 % (0.3 at 1.5 m)", "terrain_tuning_control(_r15)")
def _():
    _, a, _ = _dec("terrain_tuning_control"); _, b, _ = _dec("terrain_tuning_control_r15")
    return f"{a:.1f} % ({b:.1f} at 1.5 m)", ""
@item(70, "4.1 %", "terrain_tuning_control")
def _():
    f = float(np.median(_tune("terrain_tuning_control", "S2-flat", 0.0).column("final_dispersion")))
    g = float(np.median(_tune("terrain_tuning_control", "S2-rough", 0.0).column("final_dispersion")))
    return f"{100*(g-f)/f:.1f} %", f"S2-flat {f:.4f} vs S2-rough {g:.4f} -- S2-flat is the better FLAT-ground row"
@item(73, "+0.0421 [+0.0107, +0.0659]", "terrain_tuning_control theta_m=0.6")
def _():
    b = {x["run_index"]: x["final_dispersion"] for x in _tune("terrain_tuning_control", "S2-rough", 0.6).rows}
    return fm([x["final_dispersion"] - b[x["run_index"]] for x in _tune("terrain_tuning_control", "S2-flat", 0.6).rows if x["run_index"] in b]), ""
@item(74, "-0.0008 [-0.0134, +0.0433]", "terrain_tuning_control_r15 theta_m=0.6")
def _():
    b = {x["run_index"]: x["final_dispersion"] for x in _tune("terrain_tuning_control_r15", "S2-rough", 0.6).rows}
    return fm([x["final_dispersion"] - b[x["run_index"]] for x in _tune("terrain_tuning_control_r15", "S2-flat", 0.6).rows if x["run_index"] in b]), ""

def _reg(row, radius, n, amp, tau=None, file="terrain_regime_robustness"):
    kw = {"row": row, "start_radius": radius, "n": n, "terrain.friction_amplitude": amp}
    if tau is not None: kw["duration"] = tau
    return cells(file, **kw)
@item(75, "1.942 / 2.129", "terrain_regime_robustness")
def _():
    g = _reg("S2-gauci", 0.74, 20, 0.9).rows
    return " / ".join(fm(paired(g, _reg(r, 0.74, 20, 0.9).rows)) for r in ("S2-flat", "S2-rough")), "Gauci / row"
@item(76, "0.296 / 0.137", "terrain_regime_robustness")
def _():
    g = _reg("S2-gauci", 3.0, 20, 0.9).rows
    return " / ".join(fm(paired(g, _reg(r, 3.0, 20, 0.9).rows)) for r in ("S2-flat", "S2-rough")), "Gauci / row"
@item(77, "0.46 / 0.23 / 0.11", "terrain_regime_robustness")
def _():
    return " / ".join(fw(_reg(r, 3.0, 20, 0.9).column("ever_single_cluster")) for r in ("S2-gauci", "S2-flat", "S2-rough")), "tau=600"
@item(78, "1.00 / 0.60 / 0.34", "terrain_regime_tau")
def _():
    return " / ".join(fw(_reg(r, 3.0, 20, 0.9, tau=3600.0, file="terrain_regime_tau").column("ever_single_cluster"))
                      for r in ("S2-gauci", "S2-flat", "S2-rough")), "tau=3600"
@item(79, "0.137 / 0.141 / 0.148", "terrain_regime_tau")
def _():
    out = []
    for tau in (600.0, 1800.0, 3600.0):
        g = _reg("S2-gauci", 3.0, 20, 0.9, tau=tau, file="terrain_regime_tau").rows
        x = _reg("S2-rough", 3.0, 20, 0.9, tau=tau, file="terrain_regime_tau").rows
        out.append(f"{median_ci(paired(g, x))[0]:.3f}")
    return " / ".join(out), ""
@item(80, "0.973 / 0.870 / 0.775", "terrain_regime_robustness")
def _():
    return " / ".join(fm(paired(_reg("S2-gauci", r, 50, 0.0).rows, _reg("S2-flat", r, 50, 0.0).rows))
                      for r in (0.74, 1.5, 3.0)), "n=50 flat"
@item(81, "0.839 [0.795, 0.880]", "terrain_regime_tau_flat")
def _():
    g = _reg("S2-gauci", 3.0, 50, 0.0, tau=3600.0, file="terrain_regime_tau_flat").rows
    x = _reg("S2-flat", 3.0, 50, 0.0, tau=3600.0, file="terrain_regime_tau_flat").rows
    return fm(paired(g, x)), ""
@item(82, "140 / 280 / 330", "terrain_regime_robustness")
def _():
    return " / ".join(fm([x["time_to_first_single_cluster"] for x in _reg(r, 3.0, 20, 0.0).rows
                          if x["time_to_first_single_cluster"] is not None])
                      for r in ("S2-gauci", "S2-flat", "S2-rough")), "flat ground"

# --------------------------------------------------------------- 15, 17, 18
@item(83, "7.46 cm shared", "terrain_lambda_sweep")
def _():
    s = rec("terrain_lambda_sweep"); out = []
    for row in ("S2-gauci", "S2-rough"):
        best = None
        for L in sorted({x["terrain.correlation_length"] for x in s.rows}):
            n = s.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.9}).rows
            d = s.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.0}).rows
            if not n or not d: continue
            m = median_ci(paired(n, d))[0]
            if best is None or m > best[1]: best = (L, m)
        out.append(f"{row} {100*best[0]:.2f} cm")
    return " / ".join(out), ""
@item(84, "0.52 / 1.57", "derived from 83")
def _(): return f"{0.0746/0.1445:.2f} / {0.0746/0.0474:.2f}", "7.46 cm over each row's R0"
@item(85, "2.505 / 1.121", "terrain_lambda_sweep")
def _():
    s = rec("terrain_lambda_sweep")
    return " / ".join(fm(paired(s.filter(row=r, **{"terrain.correlation_length": 0.0746, "terrain.friction_amplitude": 0.9}).rows,
                                s.filter(row=r, **{"terrain.correlation_length": 0.0746, "terrain.friction_amplitude": 0.0}).rows))
                      for r in ("S2-gauci", "S2-rough")), ""
@item(86, "1.4267 / 1.2530, spread 0", "terrain_lambda_sweep")
def _():
    s = rec("terrain_lambda_sweep"); out = []
    for row in ("S2-gauci", "S2-rough"):
        ms = [float(np.median(s.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.0}).column("final_dispersion")))
              for L in sorted({x["terrain.correlation_length"] for x in s.rows})]
        out.append(f"{np.median(ms):.4f} (spread {max(ms)-min(ms):.4g})")
    return " / ".join(out), ""
@item(93, "0.73; 2.902", "terrain_lambda_r0_family_r074")
def _():
    r = rec("terrain_lambda_r0_family_r074"); rr = r.filter(row="R0-x2-axle-same", **{"terrain.friction_amplitude": 0.9})
    reach = [float(np.mean([1.0 if x else 0 for x in rr.filter(**{"terrain.correlation_length": L}).column("ever_single_cluster")]))
             for L in sorted({x["terrain.correlation_length"] for x in rr.rows})]
    flat = float(np.median(r.filter(row="R0-x2-axle-same", **{"terrain.friction_amplitude": 0.0}).column("final_dispersion")))
    return f"{max(reach):.2f}; {flat:.3f}", ""
@item(95, "1.01 / 0.97 diameters", "terrain_lambda_body")
def _():
    b = rec("terrain_lambda_body"); out = []
    for row, dia in (("body-base", 0.074), ("body-x2", 0.148)):
        best = None
        for L in sorted({x["terrain.correlation_length"] for x in b.rows}):
            n = b.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.9})
            d = b.filter(row=row, **{"terrain.correlation_length": L, "terrain.friction_amplitude": 0.0})
            if not len(n) or not len(d): continue
            if float(np.mean([1.0 if x else 0 for x in n.column("ever_single_cluster")])) < 0.8: continue
            m = median_ci(paired(n.rows, d.rows))[0]
            if best is None or m > best[1]: best = (L, m)
        out.append(f"{100*best[0]:.2f} cm = {best[0]/dia:.2f} d")
    return " / ".join(out), "validity window reach >= 0.8"
@item(98, "0.72; 3.057 (vs 1.427)", "terrain_lambda_body")
def _():
    b = rec("terrain_lambda_body"); rr = b.filter(row="body-half", **{"terrain.friction_amplitude": 0.9})
    reach = [float(np.mean([1.0 if x else 0 for x in rr.filter(**{"terrain.correlation_length": L}).column("ever_single_cluster")]))
             for L in sorted({x["terrain.correlation_length"] for x in rr.rows})]
    f = float(np.median(b.filter(row="body-half", **{"terrain.friction_amplitude": 0.0}).column("final_dispersion")))
    g = float(np.median(b.filter(row="body-base", **{"terrain.friction_amplitude": 0.0}).column("final_dispersion")))
    return f"{max(reach):.2f}; {f:.3f} (vs {g:.3f})", ""
@item(99, "0.0125 / 0.05 / 0.20", "derived (n r^2 / R^2)")
def _(): return " / ".join(f"{20*(d/2)**2/0.74**2:.4f}" for d in (0.037, 0.074, 0.148)), "d = 3.7 / 7.4 / 14.8 cm"

# ---------------------------------------------------------- sections 19-21
def R0(c, axle=0.051, vmax=0.128):
    l, r = c[0]*vmax, c[1]*vmax
    return abs(0.5*(l+r)*axle/(r-l))
@item(100, "1200 x 12 = 14 400", "search_s2_class_flat.json")
def _():
    s = srch("search_s2_class_flat"); return f"{s['budget_evaluations']} x {s['runs_per_evaluation']} = {s['simulation_runs']}", ""
@item(101, "7.47 / 5.53 cm", "search jsons")
def _(): return f"{100*R0(srch('search_s2_class_flat')['best_constants']):.2f} / {100*R0(srch('search_s2_flat')['best_constants']):.2f} cm", ""
@item(102, "4.47 / 4.74 cm", "search jsons")
def _(): return f"{100*R0(srch('search_s2_class_rough')['best_constants']):.2f} / {100*R0(srch('search_s2')['best_constants']):.2f} cm", ""
@item(103, "9/2/1", "terrain_class_eval")
def _():
    e = rec("terrain_class_eval"); res = {}
    for row in ("S2-class-flat", "S2-flat", "S2-rough", "S2-class-rough"):
        w = l = t = 0
        for rad in (0.74, 1.5, 3.0):
            for n in (20, 50):
                for a in (0.0, 0.9):
                    kw = {"start_radius": rad, "n": n, "terrain.friction_amplitude": a}
                    g = e.filter(row="S2-gauci", **kw).rows; x = e.filter(row=row, **kw).rows
                    if not g or not x: continue
                    m, lo, hi = median_ci(paired(g, x))
                    w, l, t = (w+1, l, t) if lo > 1 else ((w, l+1, t) if hi < 1 else (w, l, t+1))
        res[row] = f"{w}/{l}/{t}"
    return "; ".join(f"{k} {v}" for k, v in res.items()), "W = Gauci/row CI entirely above 1"
@item(104, "1.026 / 1.016 / 0.999", "terrain_class_eval")
def _():
    e = rec("terrain_class_eval")
    return " / ".join(fm(paired(e.filter(row="S2-gauci", start_radius=r, n=50, **{"terrain.friction_amplitude": 0.0}).rows,
                                e.filter(row="S2-class-flat", start_radius=r, n=50, **{"terrain.friction_amplitude": 0.0}).rows))
                      for r in (0.74, 1.5, 3.0)), ""
@item(105, "1.436 [1.249, 1.673]", "terrain_class_eval_tau")
def _():
    e = rec("terrain_class_eval_tau"); kw = {"start_radius": 3.0, "n": 20, "duration": 3600.0, "terrain.friction_amplitude": 0.9}
    return fm(paired(e.filter(row="S2-gauci", **kw).rows, e.filter(row="S2-class-flat", **kw).rows)), ""
@item(106, "1.063 [0.934, 1.172]", "terrain_class_eval_tau")
def _():
    e = rec("terrain_class_eval_tau"); kw = {"start_radius": 3.0, "n": 50, "duration": 3600.0, "terrain.friction_amplitude": 0.9}
    return fm(paired(e.filter(row="S2-gauci", **kw).rows, e.filter(row="S2-class-flat", **kw).rows)), ""
@item(107, "1.00 vs 0.86; 1.00 vs 0.95", "terrain_class_eval_tau")
def _():
    e = rec("terrain_class_eval_tau"); out = []
    for n in (20, 50):
        for row in ("S2-gauci", "S2-class-flat"):
            out.append(fw(e.filter(row=row, start_radius=3.0, n=n, duration=3600.0, **{"terrain.friction_amplitude": 0.9}).column("ever_single_cluster")))
    return " / ".join(out), "gauci n20, class n20, gauci n50, class n50"
@item(108, "140 / 245 / 280 / 330 / 340", "terrain_class_eval")
def _():
    e = rec("terrain_class_eval")
    return " / ".join(f"{np.median([x['time_to_first_single_cluster'] for x in e.filter(row=r, start_radius=3.0, n=20, **{'terrain.friction_amplitude': 0.0}).rows if x['time_to_first_single_cluster'] is not None]):.0f}"
                      for r in ("S2-gauci", "S2-class-flat", "S2-flat", "S2-rough", "S2-class-rough")), ""
@item(109, "4.47 -> 4.44 cm", "search jsons")
def _(): return f"{100*R0(srch('search_s2_class_rough')['best_constants']):.2f} -> {100*R0(srch('search_s2_class_rough_tau')['best_constants']):.2f} cm", ""
@item(110, "6 / 5 / 1", "terrain_class_tau_eval")
def _():
    e = rec("terrain_class_tau_eval"); w = l = t = 0
    for rad in (0.74, 1.5, 3.0):
        for n in (20, 50):
            for a in (0.0, 0.9):
                kw = {"start_radius": rad, "n": n, "terrain.friction_amplitude": a}
                g = e.filter(row="S2-gauci", **kw).rows; x = e.filter(row="S2-class-rough-tau", **kw).rows
                if not g or not x: continue
                m, lo, hi = median_ci(paired(g, x))
                w, l, t = (w+1, l, t) if lo > 1 else ((w, l+1, t) if hi < 1 else (w, l, t+1))
    return f"{w} / {l} / {t}", ""
@item(111, "0.26 [0.18, 0.35]", "terrain_class_tau_eval_tau")
def _():
    e = rec("terrain_class_tau_eval_tau")
    return fw(e.filter(row="S2-class-rough-tau", start_radius=3.0, n=20, duration=3600.0, **{"terrain.friction_amplitude": 0.9}).column("ever_single_cluster")), ""
def _six_cond(files, rows):
    allr = [x for f in files for x in rec(f).rows]
    conds = sorted({(x["start_radius"], x["n"], x["terrain.friction_amplitude"], x["duration"]) for x in allr})
    out = {}
    for row in rows:
        logs = [np.log(max(np.median([x["final_dispersion"] for x in allr if x["row"] == row
                and (x["start_radius"], x["n"], x["terrain.friction_amplitude"], x["duration"]) == c]), 1e-6)) for c in conds]
        out[row] = float(np.exp(np.mean(logs)))
    return out, len(conds)
@item(112, "1.6456 vs 2.6553", "terrain_class_objective_probe(_far)")
def _():
    o, nc = _six_cond(["terrain_class_objective_probe", "terrain_class_objective_probe_far"],
                      ["S2-class-flat", "S2-class-rough", "S2-class-rough-tau", "S2-gauci"])
    return f"{o['S2-class-flat']:.4f} vs {o['S2-class-rough-tau']:.4f}", \
           f"{nc} conditions; 2.6553 is S2-class-rough-TAU's, not S2-class-rough's ({o['S2-class-rough']:.4f}); Gauci {o['S2-gauci']:.4f}"
@item(113, "1.6009", "search_s2_class_rough_tau.json")
def _():
    return f"{srch('search_s2_class_rough_tau')['best_training_objective']:.4f}", \
           f"belongs to the TAU-corrected search; search_s2_class_rough is {srch('search_s2_class_rough')['best_training_objective']:.4f}"
_WORST = {"row": "S2-class-rough-tau", "start_radius": 3.0, "n": 20, "duration": 3600.0, "terrain.friction_amplitude": 0.9}
@item(114, "2.79 log units (6.98 -> 114.07)", "terrain_class_objective_probe_far")
def _():
    v = np.array(cells("terrain_class_objective_probe_far", **_WORST).column("final_dispersion"))
    rng = np.random.default_rng(0)
    two = np.median(v[rng.integers(0, v.size, (20000, 2))], axis=1)
    lo, hi = np.quantile(two, [0.05, 0.95])
    return f"{np.log(hi)-np.log(lo):.2f} log units ({lo:.2f} -> {hi:.2f})", "re-seeded resample of an ad-hoc statistic"
@item(115, "0.48 log units", "derived from 112")
def _(): return f"{abs(np.log(1.6456)-np.log(2.6553)):.2f}", ""
@item(116, "5.8x", "derived")
def _(): return f"{2.79/0.48:.1f}x", ""
@item(117, "1.14 - 242.50 (q 13.69 / 73.59)", "terrain_class_objective_probe_far")
def _():
    v = np.array(cells("terrain_class_objective_probe_far", **_WORST).column("final_dispersion"))
    return f"{v.min():.2f} - {v.max():.2f} (q {np.percentile(v,25):.2f} / {np.percentile(v,75):.2f})", ""
@item(118, "7.47 / 8.88 / 8.64; 16.9 %", "search_s2_class_flat*.json")
def _():
    v = [100*R0(srch(f"search_s2_class_flat{s}")["best_constants"]) for s in ("", "_seed2", "_seed3")]
    return f"{v[0]:.2f} / {v[1]:.2f} / {v[2]:.2f}; {100*(max(v)-min(v))/np.mean(v):.1f} %", ""
@item(120, "4 of 12", "phase0_seeds")
def _():
    p = rec("phase0_seeds"); dj = tot = 0
    for rad in (0.74, 1.5, 3.0):
        for n in (20, 50):
            for a in (0.0, 0.9):
                kw = {"start_radius": rad, "n": n, "terrain.friction_amplitude": a}
                iv = [median_ci(p.filter(row=r, **kw).column("final_dispersion")) for r in
                      ("S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3")]
                tot += 1
                if any(iv[i][2] < iv[j][1] or iv[j][2] < iv[i][1] for i in range(3) for j in range(i+1, 3)): dj += 1
    return f"{dj} of {tot}", ""
@item(121, "9/2/1, 10/0/2, 10/1/1", "phase0_seeds")
def _():
    p = rec("phase0_seeds"); out = []
    for row in ("S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3"):
        w = l = t = 0
        for rad in (0.74, 1.5, 3.0):
            for n in (20, 50):
                for a in (0.0, 0.9):
                    kw = {"start_radius": rad, "n": n, "terrain.friction_amplitude": a}
                    m, lo, hi = median_ci(paired(p.filter(row="S2-gauci", **kw).rows, p.filter(row=row, **kw).rows))
                    w, l, t = (w+1, l, t) if lo > 1 else ((w, l+1, t) if hi < 1 else (w, l, t+1))
        out.append(f"{w}/{l}/{t}")
    return ", ".join(out), ""
@item(122, "0.226 / 0.315 / 0.397", "search_s2_class_flat*.json")
def _():
    c = [np.array(srch(f"search_s2_class_flat{s}")["best_constants"]) for s in ("", "_seed2", "_seed3")]
    return f"{np.linalg.norm(c[0]-c[1]):.3f} / {np.linalg.norm(c[0]-c[2]):.3f} / {np.linalg.norm(c[1]-c[2]):.3f}", ""
@item(123, "0.252", "search_s2_class_flat_seed2.json")
def _():
    return f"{np.linalg.norm(np.array(srch('search_s2_class_flat_seed2')['best_constants']) - np.array([-0.7,-1.0,1.0,-1.0])):.3f}", ""
@item(124, "1.2143 / 1.1927 / 1.2120", "search_s2_class_flat*.json")
def _():
    return " / ".join(f"{srch(f'search_s2_class_flat{s}')['best_training_objective']:.4f}" for s in ("", "_seed2", "_seed3")), ""
@item(125, "1.2338 / 1.2246 / 1.2301", "phase0_seeds_objective_probe")
def _():
    o, nc = _six_cond(["phase0_seeds_objective_probe"], ["S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3", "S2-gauci"])
    return " / ".join(f"{o[f'S2-class-flat-s{i}']:.4f}" for i in (1, 2, 3)), f"{nc} conditions; Gauci {o['S2-gauci']:.4f}"
@item(126, "+0.019 / +0.032 / +0.018", "search jsons + phase0_seeds_objective_probe")
def _():
    rep = [srch(f"search_s2_class_flat{s}")["best_training_objective"] for s in ("", "_seed2", "_seed3")]
    o, _ = _six_cond(["phase0_seeds_objective_probe"], ["S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3"])
    return " / ".join(f"+{o[f'S2-class-flat-s{i}']-r:.4f}" for i, r in zip((1, 2, 3), rep)), ""
@item(127, "12.517 / 3.701 / 13.701", "phase0_seeds")
def _():
    p = rec("phase0_seeds")
    return " / ".join(f"{np.median(p.filter(row=r, start_radius=3.0, n=20, **{'terrain.friction_amplitude': 0.9}).column('final_dispersion')):.3f}"
                      for r in ("S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3")), "tau=600"
@item(128, "1.436 / 1.430 / 1.441", "phase0_seeds_tau")
def _():
    p = rec("phase0_seeds_tau"); kw = {"start_radius": 3.0, "n": 20, "duration": 3600.0, "terrain.friction_amplitude": 0.9}
    g = p.filter(row="S2-gauci", **kw).rows
    return " / ".join(fm(paired(g, p.filter(row=r, **kw).rows)) for r in ("S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3")), ""
@item(129, "1.00 vs 0.86 / 0.93 / 0.88", "phase0_seeds_tau")
def _():
    p = rec("phase0_seeds_tau"); kw = {"start_radius": 3.0, "n": 20, "duration": 3600.0, "terrain.friction_amplitude": 0.9}
    return " / ".join(fw(p.filter(row=r, **kw).column("ever_single_cluster"))
                      for r in ("S2-gauci", "S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3")), ""
@item(130, "1.200 / 1.166 / 1.191", "phase0_seeds")
def _():
    p = rec("phase0_seeds")
    return " / ".join(f"{np.median(p.filter(row=r, start_radius=3.0, n=50, **{'terrain.friction_amplitude': 0.0}).column('final_dispersion')):.3f}"
                      for r in ("S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3")), ""


# ===================== freeze lift 1: experiments 1-4, rows 160-193 ==========
#
# These pull from the four decision scripts rather than reimplementing their
# statistics. That is deliberate and is the same rule as everywhere else in this
# file: a number must have exactly one implementation. The decision scripts are
# it -- they apply the pre-registered rules, they use `swarm_harness.stats`
# throughout, and a second copy here could drift from the rule that decided the
# experiment without anything failing.
#
# Each is imported lazily and memoised, because experiment 4's costs a few
# seconds and most runs of this script do not need it.

import importlib.util as _ilu, io as _io, contextlib as _ctx

_DEC: dict[str, dict] = {}
def dec(name: str, *flags: str) -> dict:
    """Run a decision script with --json and return its parsed output."""
    key = name + " ".join(flags)
    if key not in _DEC:
        spec = _ilu.spec_from_file_location(f"_d_{key}", REPO / "scripts" / f"{name}.py")
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        argv, sys.argv = sys.argv, ["x", "--json", *flags]
        buf = _io.StringIO()
        try:
            with _ctx.redirect_stdout(buf):
                mod.main()
        finally:
            sys.argv = argv
        t = buf.getvalue()
        _DEC[key] = json.loads(t[t.index("\n{"):])
    return _DEC[key]

def ci(d, k="value", lo="lo", hi="hi", p=4):
    return f"{d[k]:+.{p}f} [{d[lo]:+.{p}f}, {d[hi]:+.{p}f}]"

# ------------------------------------------------- experiment 1, §22 --------
def _s3(file, row, h=1.93, **kw):
    return cells(file, row=row, **{"pursuer.handling_time": h}, **kw)
def _perrobot(rows):
    f = []
    for x in rows:
        n, sv = int(x["n"]), int(x["survivors"]); f.extend([1.0]*sv + [0.0]*(n-sv))
    pv, lo, hi = wilson_ci(f); return pv, lo, hi

S3_TASK = ("S3-survival_task-s1", "S3-survival_task-s2", "S3-survival_task-s3")
S3_SURV = ("S3-survival-s1", "S3-survival-s2", "S3-survival-s3")

def _cellwise(reference, rows, file="pursuer_searched_s3"):
    """Per (r_p, kappa) cell at h = 1.93: does best-of-`rows` beat `reference`?

    Best-of-three is per cell, per §21 branch (b). Returns (better, worse,
    overlap, per-seed better counts) on mean per-robot survival with Wilson
    intervals -- §12.1 D0's statistic, never a median of survival_fraction.
    """
    r = rec(file)
    rps = sorted({x["pursuer.range"] for x in r.rows})
    ks = sorted({x["pursuer.confusion"] for x in r.rows})
    better = worse = overlap = 0
    per_seed = [0]*len(rows)
    for rp in rps:
        for k in ks:
            kw = {"pursuer.range": rp, "pursuer.confusion": k}
            ref = _perrobot(_s3(file, reference, **kw).rows)
            best = max((_perrobot(_s3(file, row, **kw).rows) for row in rows), key=lambda t: t[0])
            for i, row in enumerate(rows):
                if _perrobot(_s3(file, row, **kw).rows)[1] > ref[2]:
                    per_seed[i] += 1
            if best[1] > ref[2]: better += 1
            elif best[2] < ref[1]: worse += 1
            else: overlap += 1
    return better, worse, overlap, per_seed

@item(163, "18 of 25 (0 worse; per seed 18 / 17 / 14)", "pursuer_searched_s3")
def _():
    b, w, o, ps = _cellwise("B0-blind", S3_TASK)
    return (f"{b} of {b+w+o} ({w} worse, {o} overlapping; per seed {' / '.join(map(str, ps))})",
            "best-of-three per cell, §21 branch (b)")
@item(164, "1.41 vs 1.45", "pursuer_searched_s3")
def _():
    """Dispersion among survivors for the BEST-OF-THREE SELECTION, not pooled.

    Pooling all three seeds' runs answers a different question and gives 1.46:
    the claim is about the row that won each cell, so the selection has to be
    made per cell before the dispersions are pooled -- §21 branch (b) again.
    """
    r = rec("pursuer_searched_s3")
    rps = sorted({x["pursuer.range"] for x in r.rows})
    ks = sorted({x["pursuer.confusion"] for x in r.rows})
    picked, ref = [], []
    for rp in rps:
        for k in ks:
            kw = {"pursuer.range": rp, "pursuer.confusion": k}
            best = max(S3_TASK, key=lambda row: _perrobot(_s3("pursuer_searched_s3", row, **kw).rows)[0])
            picked += [x["final_dispersion"] for x in _s3("pursuer_searched_s3", best, **kw).rows
                       if x["survivors"] >= 3]
            ref += [x["final_dispersion"] for x in _s3("pursuer_searched_s3", "B0-blind", **kw).rows
                    if x["survivors"] >= 3]
    return (f"{np.median(picked):.2f} vs {np.median(ref):.2f}",
            f"{fm(picked)} vs {fm(ref)}; best-of-three chosen per cell, then pooled")
@item(165, "13 of 25", "pursuer_searched_s3")
def _():
    b, w, o, _ps = _cellwise("B1-ternary", ("S3-survival_task-s2",))
    return f"{b} of {b+w+o}", f"{w} worse, {o} overlapping -- rule (a), seed 2 alone"
@item(166, "0.5125 / 0.4596 / 0.3655", "pursuer_searched_s3")
def _():
    return " / ".join(f"{_perrobot(_s3('pursuer_searched_s3', r).rows)[0]:.4f}"
                      for r in ("S3-survival_task-s2", "B1-ternary", "B0-blind")), "pooled at h = 1.93"
@item(167, "14 492 / 10 872 / 9 744", "pursuer_searched_s3")
def _():
    return " / ".join(f"{np.median([x['final_dispersion'] for x in _s3('pursuer_searched_s3', r).rows if x['survivors'] >= 3]):.0f}"
                      for r in S3_SURV), "dispersion among survivors, survival-only rows"
@item(168, "0 / 0 / 0 runs with <= 5 survivors", "pursuer_searched_s3")
def _():
    out = []
    for r in S3_SURV + ("D-dispersive", "B1-ternary"):
        c = _s3("pursuer_searched_s3", r).rows
        usable = [x for x in c if x["survivors"] >= 3]
        le5 = sum(1 for x in usable if x["survivors"] <= 5)
        out.append(f"{r.split('-')[-1]} {le5}/{len(usable)} ({100*le5/len(usable):.1f}%)")
    return " ".join(out[:3]), "and " + "; ".join(out[3:]) + " -- share of USABLE runs"
@item(169, "0.6795 vs 0.7040 at 1.39 vs 379.90", "pursuer_searched_s3_pareto")
def _():
    kw = {"pursuer.range": 0.2, "pursuer.confusion": 0.0, "pursuer.handling_time": 1.93}
    out = []
    for r in ("S3-survival_task-s2", "D-dispersive"):
        c = cells("pursuer_searched_s3_pareto", row=r, **kw)
        sv = _perrobot(c.rows)[0]
        d = np.median([x["final_dispersion"] for x in c.rows if x["survivors"] >= 3])
        out.append(f"{sv:.4f} at {d:.2f}")
    return " vs ".join(out), "r_p = 0.2 m, kappa = 0; task quality ratio"

# ------------------------------------------------- experiment 2, §23 --------
@item(170, "1.0412 / 1.1277 / 1.1175 at n = 50", "terrain_capability_n")
def _():
    d = dec("experiment2_decision")["n=50"]
    h = d["hold_ratios"]
    return (f"{h[d['best_s2']][0]:.4f} / {h['S4-terrain'][0]:.4f} / {h['S4-warm'][0]:.4f}",
            f"best S = 2 is {d['best_s2']}; {d['verdict']}")
@item(171, "1.1449 / 1.0490 / 1.1158 at n = 10, tau = 3600 s", "terrain_capability_n_tau")
def _():
    d = dec("experiment2_decision")["n=10,tau=3600"]
    h = d["hold_ratios"]
    return (f"{h[d['best_s2']][0]:.4f} / {h['S4-terrain'][0]:.4f} / {h['S4-warm'][0]:.4f}",
            f"best S = 2 is {d['best_s2']}; {d['verdict']}")
@item(172, "0.71 -> 1.00", "terrain_capability_n(_tau)")
def _():
    a = fw(cells("terrain_capability_n", row="S2-gauci",
                 **{"swarm.n": 10, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    b = fw(cells("terrain_capability_n_tau", row="S2-gauci",
                 **{"swarm.n": 10, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    return f"{a} -> {b}", "the pre-registered tau contingency firing on Gauci alone"
@item(173, "0.0069", "terrain_capability_n_tau")
def _():
    d = dec("experiment2_decision")["n=10,tau=3600"]
    s4 = d["s4"]["S4-terrain"]; best = d["hold_ratios"][d["best_s2"]]
    return f"{s4['hi'] - best[1]:.4f}", "S4-terrain upper bound minus best S = 2 lower bound"

# ------------------------------------------------- experiment 3, §24 --------
@item(174, "+0.0951 / +0.0818 / +0.0368", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")["per_lambda"]
    return " / ".join(ci(d[k]["terrain_term"]["0.9"]) for k in ("0.05", "0.1", "0.2")), \
           "paired terrain term at theta_m = 0.9, lambda 0.05 / 0.10 / 0.20 m"
@item(175, "95.0 / 96.9 / 94.4 % objective-tuning", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")["per_lambda"]
    return (" / ".join(f"{d[k]['decomposition']['objective_pct']:.1f}" for k in ("0.05", "0.1", "0.2")),
            "terrain share " + " / ".join(f"{d[k]['decomposition']['terrain_pct']:.1f}" for k in ("0.05", "0.1", "0.2")))
@item(176, "+1.2 % to +21.4 %", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")["matched_controller_cost"]
    return f"{d['range_pct'][0]:+.1f} % to {d['range_pct'][1]:+.1f} %", \
           "range over three lambda and both tuned rows, §12.1 D1 paired form"
@item(177, "+0.0659 / +0.0421 / -0.0160 at theta_m = 0.6", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")["crossing"]
    return " / ".join(ci(d["per_lambda"][k]) for k in ("0.05", "0.1", "0.2")), \
           f"disjoint at {len(d['disjoint_at'])} of 3 -> claimed = {d['claimed']}"
@item(178, "2.0719 / 2.1492 / 1.5186", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")["per_lambda"]
    return " / ".join(f"{d[k]['hold_ratios']['S2-gauci']['value']:.4f}" for k in ("0.05", "0.1", "0.2")), \
           "the anchor's own hold ratio; the gap being decomposed shrinks with it"
@item(179, "600 of 600, 0 disagreements", "terrain_tuning_control(_lambda)")
def _():
    d = dec("experiment3_decision")
    n = 3 * 2 * 100   # three rows x two new lambda x 100 run indices
    return (f"{n} of {n}, 0 disagreements" if d["pairing_exact"] else "BROKEN"), \
           "run i is the same seed and initial dispersion at every lambda"

# ------------------------------------------------- experiment 4, §25 --------
def _e4(*flags):
    return dec("experiment4_decision", *flags)
def _counts(d, name):
    e = d["orderings"][name]
    return f"{e['same_sign']}/{e['disjoint']}/{e['flips']}"

@item(180, "10/10/0 ROBUST", "pseudo_reality_aggregation_model_*")
def _():
    d = _e4(); n = "C1 — hold-ratio difference at θ_m = 0.9"
    return f"{_counts(d, n)} {d['orderings'][n]['verdict']}", "comparison 1, same-sign/disjoint/flips of 10"
@item(181, "9/4/1 not established either way", "pseudo_reality_aggregation_model_*")
def _():
    d = _e4(); n = "C2 — hold-ratio difference at θ_m = 0.9, n = 20"
    e = d["orderings"][n]
    fl = e["flipping_models"][0]
    return (f"{_counts(d, n)} {e['verdict']}",
            f"the flip is model {fl:02d} at {ci(e['per_model'][str(fl)])}")
@item(182, "1 of 10 disjointly BETTER (model 09)", "pseudo_reality_aggregation_model_*")
def _():
    d = _e4(); e = d["orderings"]["C2 — hold-ratio difference at θ_m = 0.9, n = 20"]
    better = [m for m, v in e["per_model"].items() if v["hi"] < 0]
    return (f"{len(better)} of 10", "A1 AS WORDED asks whether any S = 4 row is disjointly BETTER; "
            + (f"model(s) {', '.join(better)}" if better else "none") + "; reference: no")
@item(183, "ROBUST / ROBUST / ROBUST", "pseudo_reality_pursuit_model_*")
def _():
    d = _e4()
    ns = [f"C3 — κ-response ratio — {r}" for r in ("B0-blind", "B1-ternary", "D-dispersive")]
    return " / ".join(d["orderings"][n]["verdict"] for n in ns), \
           " / ".join(_counts(d, n) for n in ns)
@item(184, "not established / ROBUST / ROBUST", "pseudo_reality_pursuit_model_*")
def _():
    d = _e4()
    ns = [f"C4 — B1 − D — r_p = {r} m" for r in ("0.1", "0.35", "1")]
    return " / ".join(d["orderings"][n]["verdict"] for n in ns), \
           " / ".join(_counts(d, n) for n in ns)
@item(185, "1 fragile ordering of 14: C5 vs B1 at r_p = 1 m", "pseudo_reality_pursuit_model_*")
def _():
    d = _e4()
    frag = [n for n, e in d["orderings"].items() if e["verdict"] == "FRAGILE"]
    n = "C5 — S3† − B1-ternary — r_p = 1 m"
    e = d["orderings"][n]
    # The counts are spelled "x of 10" rather than "x/y/z" because §13 states
    # them that way and the row has to read as one sequence in both documents.
    return (f"{len(frag)} of 14 orderings FRAGILE: {'; '.join(frag)}",
            f"{e['same_sign']}/10 same sign, {e['disjoint']}/10 disjoint, "
            f"{e['flips']}/10 flips, all of them dt = 0.05 models "
            + ", ".join(f"{m:02d}" for m in e["flipping_models"]))
@item(186, "0.65 lowest, S2-gauci in model 05", "pseudo_reality_aggregation_model_*")
def _():
    d = _e4()["reach_diagnostic"]
    lo = min((v, m, r) for m, row in d.items() for r, v in row.items())
    return f"{lo[0]:.2f} ({lo[2]} in model {int(lo[1]):02d})", \
           f"reference {d['0']['S2-gauci']:.2f}; reported, NOT thresholded"
@item(187, "1 flip in 14 orderings, model-only", "pseudo_reality_*_model_*")
def _():
    d = _e4("--fixed2")["d10_split"]
    only = [n for n, v in d.items() if not v["model_plus_control_period"].startswith("5/5 sign")
            and v["model_only"].startswith("5/5 sign")]
    flips = [n for n, v in d.items() if not v["model_only"].startswith("5/5 sign")]
    return (f"{len(flips)} of {len(d)}: {'; '.join(flips) or 'none'}",
            f"and {len(only)} ordering(s) flip only in the control-period half")
@item(188, "0.9050 -> 0.6150 noise-free, DISJOINT", "dt_reach_noisefree")
def _():
    r = rec("dt_reach_noisefree")
    a = fw(r.filter(row="S2-gauci", **{"sim.dt": 0.1, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    b = fw(r.filter(row="S2-gauci", **{"sim.dt": 0.05, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    c = fw(r.filter(row="S2-searched", **{"sim.dt": 0.1, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    e = fw(r.filter(row="S2-searched", **{"sim.dt": 0.05, "terrain.friction_amplitude": 0.9}).column("ever_single_cluster"))
    return f"{a} -> {b}", f"S2-searched {c} -> {e}; 400 runs/cell, seed base 20260911, wheel_noise = 0"
@item(189, "2.0739 -> 2.9747 hold ratio, noise-free", "dt_reach_noisefree")
def _():
    r = rec("dt_reach_noisefree")
    out = []
    for dt in (0.1, 0.05):
        kw = {"sim.dt": dt}
        num = r.filter(row="S2-gauci", **kw, **{"terrain.friction_amplitude": 0.9}).rows
        den = r.filter(row="S2-gauci", **kw, **{"terrain.friction_amplitude": 0.0}).rows
        m, lo, hi = median_ci(paired(num, den))
        out.append(f"{m:.4f} [{lo:.4f}, {hi:.4f}]")
    return " -> ".join(out), "the enumerated row's terrain tax at two control periods"


def main():
    RESULTS.sort(key=lambda r: r["id"])
    if "--json" in sys.argv:
        print(json.dumps(RESULTS, indent=1)); return 0
    print(f"{'#':>4}  {'claimed':<34}  {'recomputed':<44}  note")
    for r in RESULTS:
        print(f"{r['id']:>4}  {r['claimed'][:34]:<34}  {str(r['recomputed'])[:44]:<44}  {r['note'][:90]}")
    print(f"\n{len(RESULTS)} of 189 rows recomputed from logged runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
