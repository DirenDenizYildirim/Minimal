"""Question A, experiment 1: what sets the peak correlation length?

Section 15 compared two controllers differing in every constant, so "the peak is
at a fixed λ, not a fixed λ/R₀" could still have been a fact about one searched
row. These three rows are the same Gauci table with only the state-0 forward
constant changed: the sensor model, the state-1 spin and the axle are identical
and R₀ is the only thing that moves.

Two start radii. 1.5 m is what the experiment asked for; 0.74 m is §15's
condition, added because at 1.5 m the measurement stops working — see the
validity window below. The decision rule is applied to the 0.74 m row of panels.

**Validity window.** A hold ratio only means "how much looser is the cluster"
while there *is* a cluster. Where reach at θ_m = 0.9 falls below 0.8 the ratio is
driven by runs that never aggregated, and a peak read there is a peak in
failure, not in holding. Points outside the window are drawn hollow and are
excluded from every peak. The threshold was fixed after seeing the 1.5 m sweep,
so its use there is post hoc and labelled; for the 0.74 m sweep it was fixed in
advance.

Peaks carry a bootstrap CI over run indices — one resample of the paired index
set per replicate, applied to every λ and every row at once, then argmax — which
also gives a CI on the *ratio* between two rows' peaks. That ratio is the
experiment: 2.0 if the peak follows R₀, 1.0 if the length scale is fixed.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import bootstrap_ci, wilson_ci

SUPTITLE = (
    "Question A, experiment 1: doubling R₀ does not double the worst λ.  Three rows of Gauci's table differing only in the\n"
    "state-0 forward constant, so R₀ is the only thing that moves.  θ_m = 0.9, n = 20, τ = 600 s, 100 runs/cell, λ = 2 → 38.6 cm.\n"
    "At 0.74 m the two measurable rows peak at 5.37 and 7.46 cm for R₀ = 7.23 and 14.45 cm: a peak ratio of 1.39 [0.72, 1.93],\n"
    "which EXCLUDES the ratio law's 2.00 and CONTAINS a fixed scale's 1.00.  R₀-x2 never reaches a cluster in 80% of runs at\n"
    "any λ — its own turning circle is 39% of the start radius — so it yields no peak, at either start radius."
)
SWEEPS = [
    ("results/terrain_lambda_r0_family_r074.jsonl", 0.74,
     "start radius 0.74 m — §15's condition, and the one the decision rule is read from"),
    ("results/terrain_lambda_r0_family.jsonl", 1.5,
     "start radius 1.5 m — §14's realistic radius, where the metric stops working"),
]
ROWS = ["R0-half-axle-same", "base", "R0-x2-axle-same"]
colours = {"R0-half-axle-same": "#1f77b4", "base": "#ff7f0e", "R0-x2-axle-same": "#2ca02c"}
REACH_FLOOR = 0.8
PEAK_RATIO = 0.52  # the base row's measured λ/R₀ in §15, used for the predictions
BOOT = 2000


def analyse(path):
    r = load_jsonl(path)
    lams = r.unique("terrain.correlation_length")
    ams = r.unique("terrain.friction_amplitude")
    out = {}
    for row in ROWS:
        r0 = {x["state0_turn_radius"] for x in r.filter(row=row).rows}
        assert len(r0) == 1, (row, r0)
        keys, cols, reach = None, [], []
        for lam in lams:
            flat = {x["run_index"]: x["final_dispersion"]
                    for x in r.filter(row=row, **{"terrain.correlation_length": lam,
                                                  "terrain.friction_amplitude": min(ams)}).rows}
            rough = r.filter(row=row, **{"terrain.correlation_length": lam,
                                         "terrain.friction_amplitude": max(ams)})
            rough_d = {x["run_index"]: x["final_dispersion"] for x in rough.rows}
            ks = sorted(set(flat) & set(rough_d))
            keys = ks if keys is None else keys
            assert ks == keys, "run indices differ between cells; the pairing is broken"
            cols.append([rough_d[k] / flat[k] for k in ks])
            reach.append(wilson_ci(rough.column("ever_single_cluster")))
        out[row] = dict(r0=r0.pop(), lams=lams, matrix=np.asarray(cols).T,
                        reach=reach, records=r.filter(row=row))
    return out


def peak(d, rng, resample=None):
    """argmax λ inside the validity window, on a resample of the run indices."""
    m = d["matrix"] if resample is None else d["matrix"][resample]
    curve = np.median(m, axis=0)
    ok = [j for j, (p, _, _) in enumerate(d["reach"]) if p >= REACH_FLOOR]
    if not ok:
        return None
    return d["lams"][max(ok, key=lambda j: curve[j])]


fig, axes = plt.subplots(2, 2, figsize=(13.0, 10.4))
report = {}

for ri, (path, radius, title) in enumerate(SWEEPS):
    data = analyse(path)
    rng = np.random.default_rng(20260905)
    n_runs = data[ROWS[0]]["matrix"].shape[0]
    draws = [rng.integers(0, n_runs, n_runs) for _ in range(BOOT)]
    peaks = {row: [peak(data[row], rng, d) for d in draws] for row in ROWS}
    report[radius] = {}

    for row in ROWS:
        d = data[row]
        mid = np.median(d["matrix"], axis=0)
        lo, hi = zip(*[bootstrap_ci(d["matrix"][:, j]) for j in range(len(d["lams"]))])
        inside = [p >= REACH_FLOOR for p, _, _ in d["reach"]]
        label = f"{_label(row, d['records'])}  (R₀ = {d['r0'] * 100:.2f} cm)"
        for ci, xs in ((0, d["lams"]), (1, [lam / d["r0"] for lam in d["lams"]])):
            ax = axes[ri][ci]
            ax.plot(xs, mid, color=colours[row], lw=1.4, label=label if ci == 0 else None)
            ax.fill_between(xs, lo, hi, alpha=0.14, color=colours[row], lw=0)
            for x, y, ok in zip(xs, mid, inside):
                ax.plot([x], [y], marker="o", ms=5, color=colours[row],
                        mfc=colours[row] if ok else "white", mew=1.3)
        pk = peak(d, rng)
        ps = [p for p in peaks[row] if p is not None]
        if pk is None:
            report[radius][row] = None
            print(f"r0={radius} {row:>18} R0={d['r0']*100:5.2f}cm  NO VALID λ "
                  f"(reach < {REACH_FLOOR} at every λ; max {max(p for p,_,_ in d['reach']):.2f})")
        else:
            plo, phi = np.percentile(ps, [2.5, 97.5])
            report[radius][row] = (pk, plo, phi, peaks[row])
            print(f"r0={radius} {row:>18} R0={d['r0']*100:5.2f}cm  peak λ = {pk*100:6.2f} cm "
                  f"[{plo*100:.2f}, {phi*100:.2f}]  λ/R₀ = {pk/d['r0']:.2f}  "
                  f"ratio-law prediction {PEAK_RATIO*d['r0']*100:.2f} cm  "
                  f"({sum(inside)}/{len(inside)} λ inside the window)")

    # The experiment, as one number: how far apart are two rows' peaks, when
    # their R0 differ by 2x? Paired, because both rows share the run-index axis.
    for a, b in (("R0-half-axle-same", "base"), ("base", "R0-x2-axle-same")):
        pa, pb = peaks[a], peaks[b]
        ratios = [y / x for x, y in zip(pa, pb) if x and y]
        if len(ratios) > BOOT // 4:
            r_lo, r_hi = np.percentile(ratios, [2.5, 97.5])
            point = report[radius][b][0] / report[radius][a][0] if (
                report[radius][a] and report[radius][b]) else float("nan")
            print(f"    peak ratio {b}/{a} = {point:.2f} [{r_lo:.2f}, {r_hi:.2f}]  "
                  f"(ratio law predicts 2.00, fixed scale predicts 1.00)")

for ri, (_, radius, title) in enumerate(SWEEPS):
    for ci, (xlabel, ticks) in enumerate((
        ("terrain.correlation_length  λ  (m)", [0.02, 0.05, 0.1, 0.2, 0.4]),
        ("λ / R₀   (each row by its OWN R₀)", [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]),
    )):
        ax = axes[ri][ci]
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.axhline(1.0, color="0.5", ls=":", lw=1.0)
        ax.set_xlabel(xlabel, fontsize=9)
        ax.grid(alpha=0.25, lw=0.6)
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.yaxis.set_major_formatter(ScalarFormatter())
    axes[ri][0].set_ylabel(f"{title}\n\nhold ratio (log)\nθ_m = 0.9 / own flat ground, paired, 95%",
                           fontsize=9)
    axes[ri][1].axvline(PEAK_RATIO, color="0.35", ls=":", lw=1.4)
    axes[ri][1].annotate(f"λ/R₀ = {PEAK_RATIO}", xy=(PEAK_RATIO, 0.02),
                         xycoords=("data", "axes fraction"), xytext=(4, 0),
                         textcoords="offset points", fontsize=8, color="0.3")
axes[0][0].legend(fontsize=8.5, frameon=False, loc="upper left")
axes[0][0].plot([], [], marker="o", ms=5, ls="none", color="0.4", mfc="white", mew=1.3,
                label=f"hollow: reach < {REACH_FLOOR} at θ_m = 0.9, excluded from the peak")
axes[0][0].legend(fontsize=8.5, frameon=False, loc="upper left")

fig.suptitle(SUPTITLE, fontsize=9, y=0.997, va="top")
fig.subplots_adjust(top=0.855, bottom=0.075, left=0.10, right=0.985, hspace=0.30, wspace=0.13)
fig.text(0.5, 0.012, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_lambda_r0_family.png", dpi=160)
print("wrote figures/terrain_lambda_r0_family.png")
