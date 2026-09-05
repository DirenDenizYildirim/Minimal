"""Experiment 1's decision rule at two start radii.

Experiment 1 found branch (c) — S2-flat and S2-rough cross — at the start radius
both were tuned at. Experiment 2 then found the searched rows' advantage over
Gauci to be regime-specific, which makes "where was the rule measured?" a live
question rather than a caption. This re-runs the identical paired test at 1.5 m,
the largest radius at which both searched rows still beat Gauci, and puts the two
side by side.

Both panels are the same statistic: median of (S2-flat − S2-rough) taken run by
run, so each difference is one initial placement and one traction field seen by
both controllers, with a bootstrap 95% interval on the median.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE
from swarm_harness.stats import bootstrap_ci

PANELS = [
    ("results/terrain_tuning_control.jsonl", 0.74,
     "start radius 0.74 m — the tuned condition (§13)"),
    ("results/terrain_tuning_control_r15.jsonl", 1.5,
     "start radius 1.5 m — the largest radius where both still beat Gauci"),
]

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9), sharey=True)

for ax, (path, radius, title) in zip(axes, PANELS):
    r = load_jsonl(path)
    ams = r.unique("terrain.friction_amplitude")
    mid, los, his, verdict = [], [], [], []
    for a in ams:
        f = {x["run_index"]: x["final_dispersion"]
             for x in r.filter(row="S2-flat", **{"terrain.friction_amplitude": a}).rows}
        g = {x["run_index"]: x["final_dispersion"]
             for x in r.filter(row="S2-rough", **{"terrain.friction_amplitude": a}).rows}
        keys = sorted(set(f) & set(g))
        d = np.array([f[k] - g[k] for k in keys])
        lo, hi = bootstrap_ci(d)
        mid.append(float(np.median(d)))
        los.append(lo)
        his.append(hi)
        verdict.append("flat" if hi < 0 else ("rough" if lo > 0 else None))
    ax.axhline(0.0, color="0.4", ls="--", lw=1.0)
    ax.plot(ams, mid, marker="o", ms=5, color="#7f2f8f")
    ax.fill_between(ams, los, his, alpha=0.20, color="#7f2f8f", lw=0)
    # Mark only the points whose interval excludes zero: the rule turns on those,
    # and a reader should not have to infer significance from a band's edge.
    for a, m, v in zip(ams, mid, verdict):
        if v is not None:
            ax.plot([a], [m], marker="o", ms=10, mfc="none", mec="#7f2f8f", mew=1.8)
    ax.set_title(title, fontsize=9.5)
    ax.set_xlabel("terrain.friction_amplitude  (θ_m)")
    ax.grid(alpha=0.25, lw=0.6)

axes[0].set_ylabel("paired difference  S2-flat † − S2-rough †\n"
                   "(matched run index, median, bootstrap 95%)", fontsize=9)
for ax in axes:
    ax.annotate("S2-flat better", xy=(0.02, 0.06), xycoords="axes fraction",
                fontsize=8, color="0.35")
    ax.annotate("S2-rough better", xy=(0.02, 0.92), xycoords="axes fraction",
                fontsize=8, color="0.35")

fig.suptitle(
    "Experiment 1's decision rule is regime-specific.  n = 20, λ = 0.10 m, τ = 600 s, 100 runs/cell, held-out seeds\n"
    "Left: branch (c) — they cross, and S2-rough is significantly better at θ_m = 0.6 (ringed).\n"
    "Right: at twice the start radius the crossing is gone. S2-flat is better at θ_m ≤ 0.3 and nothing is\n"
    "significant above it — branch (b): terrain does not move the optimum, it taxes a fixed controller.",
    fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.775, bottom=0.175, left=0.115, right=0.98, wspace=0.07)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_decision_rule_regimes.png", dpi=160)
print("wrote figures/terrain_decision_rule_regimes.png")
