"""Experiment 2: does the searched controllers' advantage survive outside the
initial condition they were tuned in?

Three panel-rows, two panel-columns (n = 20, n = 50), start radius on the x
axis. Reach and absolute dispersion are what the experiment asked for; the hold
ratio is added because it is the statistic section 13's headline is stated in
(1.195 against 2.208), and an advantage that survives on the absolute axis but
not on the ratio would otherwise be invisible.

Every point is paired by run index across the three rows: the same initial
placement and the same traction field, so the ratios below are per-run and not
between independent medians.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import bootstrap_ci, median_ci, wilson_ci

r = load_jsonl("results/terrain_regime_robustness.jsonl")
ROWS = ["S2-gauci", "S2-flat", "S2-rough"]
RAD = r.unique("swarm.init.radius")
NS = r.unique("swarm.n")
AMS = r.unique("terrain.friction_amplitude")
TUNED_RADIUS = 0.74
colours = {"S2-gauci": "#ff7f0e", "S2-flat": "#1f77b4", "S2-rough": "#2ca02c"}
styles = {min(AMS): (0, (4, 2)), max(AMS): "-"}


def cell(row, a, rad, n):
    return r.filter(row=row, **{"terrain.friction_amplitude": a,
                                "swarm.init.radius": rad, "swarm.n": n})


def paired(row, a, rad, n, other_a=None, other_row=None):
    """Per-run values of `row` divided by a matched-run reference."""
    num = {x["run_index"]: x["final_dispersion"] for x in cell(row, a, rad, n).rows}
    den = {x["run_index"]: x["final_dispersion"]
           for x in cell(other_row or row, other_a if other_a is not None else a, rad, n).rows}
    keys = sorted(set(num) & set(den))
    return np.array([num[k] / den[k] for k in keys])


SUPTITLE = (
    "Experiment 2: the searched rows' advantage does NOT survive outside the initial condition they were tuned in\n"
    "λ = 0.10 m, τ = 600 s, 100 runs/cell, held-out seeds.  Grey dashed vertical: the start radius both searches were run at.\n"
    "At 4× that radius under terrain the ordering INVERTS — S2-rough reaches a cluster in 11% of runs against Gauci's 46%.\n"
    "Extending τ sixfold (§14) lifts Gauci to 1.00 and S2-rough only to 0.34, so that cell is a failure, not slowness.\n"
    "At n = 50 the searched rows are worse than Gauci on flat ground at every radius, and τ = 3600 s does not close it."
)

fig, axes = plt.subplots(3, len(NS), figsize=(11.0, 10.6), sharex=True, squeeze=False)
handles: dict[str, object] = {}

for ci, n in enumerate(NS):
    for row in ROWS:
        for a in AMS:
            sub = r.filter(row=row, **{"terrain.friction_amplitude": a, "swarm.n": n})
            name = f"{_label(row, sub)}, θ_m = {a:g}"
            for ri, summ, field in ((0, wilson_ci, "ever_single_cluster"),
                                    (1, median_ci, "final_dispersion")):
                m, lo, hi = zip(*[summ(cell(row, a, rad, n).column(field)) for rad in RAD])
                line, = axes[ri][ci].plot(RAD, m, marker="o", ms=4, color=colours[row],
                                          ls=styles[a], label=name)
                axes[ri][ci].fill_between(RAD, lo, hi, alpha=0.14, color=colours[row], lw=0)
                if ri == 0:
                    handles.setdefault(name, line)
        # Hold ratio: theta_m = 0.9 against this row's own flat ground, per run.
        stats = [bootstrap_ci(paired(row, max(AMS), rad, n, other_a=min(AMS))) for rad in RAD]
        mid = [float(np.median(paired(row, max(AMS), rad, n, other_a=min(AMS)))) for rad in RAD]
        axes[2][ci].plot(RAD, mid, marker="o", ms=4.5, color=colours[row])
        axes[2][ci].fill_between(RAD, [s[0] for s in stats], [s[1] for s in stats],
                                 alpha=0.16, color=colours[row], lw=0)
    axes[2][ci].axhline(1.0, color="0.45", ls=":", lw=1.0)
    axes[0][ci].set_title(f"n = {n:g}", fontsize=10)
    for ri in range(3):
        ax = axes[ri][ci]
        ax.axvline(TUNED_RADIUS, color="0.55", ls="--", lw=1.0, zorder=0)
        ax.grid(alpha=0.25, lw=0.6)
    axes[2][ci].set_xlabel("swarm.init.radius  (m)")
    axes[0][ci].annotate("tuned here", xy=(TUNED_RADIUS, 0.02), xycoords=("data", "axes fraction"),
                         xytext=(4, 0), textcoords="offset points", fontsize=7.5, color="0.4")

axes[0][0].set_ylabel("reach\n(Wilson 95%)", fontsize=9)
axes[1][0].set_ylabel("final dispersion\n(absolute, median, 95%)", fontsize=9)
axes[2][0].set_ylabel("hold ratio\nθ_m = 0.9 / own flat ground\n(paired by run index, 95%)",
                      fontsize=9)
axes[1][0].set_yscale("log")
axes[1][1].set_yscale("log")

fig.legend(list(handles.values()), list(handles.keys()), loc="lower center", ncol=3,
           fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.035))
fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.885, bottom=0.135, left=0.135, right=0.975, hspace=0.13, wspace=0.16)
fig.text(0.5, 0.008, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_regime_robustness.png", dpi=160)
print("wrote figures/terrain_regime_robustness.png")
