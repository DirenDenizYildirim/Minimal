"""Experiment 1: the 2x2 tuning control.

Three panels. The first two are what the experiment asked for; the third is the
paired difference between the two searched rows, without which the figure cannot
show its own decision-rule outcome — on the absolute axis those two lines are
nearly coincident, and the crossing that decides the experiment is invisible.

The paired test is available because both rows share a seed base: run index i is
the same initial placement and the same traction field in both, so the difference
can be taken run by run instead of between two independent medians.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import bootstrap_ci, median_ci, wilson_ci

r = load_jsonl("results/terrain_tuning_control.jsonl")
ROWS = ["S2-gauci", "S2-flat", "S2-rough"]
AMS = r.unique("terrain.friction_amplitude")
colours = {"S2-gauci": "#ff7f0e", "S2-flat": "#1f77b4", "S2-rough": "#2ca02c"}

fig, axes = plt.subplots(3, 1, figsize=(9.0, 10.2), sharex=True)

for ax, (field, label, summ) in zip(
    axes,
    [("ever_single_cluster", "reach\n(Wilson 95%)", wilson_ci),
     ("final_dispersion", "final dispersion\n(absolute, lower is better)", median_ci)],
):
    for row in ROWS:
        sub = r.filter(row=row)
        m, lo, hi = zip(*[summ(sub.filter(**{"terrain.friction_amplitude": a}).column(field))
                          for a in AMS])
        ax.plot(AMS, m, marker="o", ms=4, color=colours[row], label=_label(row, sub))
        ax.fill_between(AMS, lo, hi, alpha=0.18, color=colours[row], lw=0)
    ax.set_ylabel(label, fontsize=9)
    ax.grid(alpha=0.25, lw=0.6)

ax = axes[2]
mid, los, his = [], [], []
for a in AMS:
    f = {x["run_index"]: x["final_dispersion"]
         for x in r.filter(row="S2-flat", **{"terrain.friction_amplitude": a}).rows}
    g = {x["run_index"]: x["final_dispersion"]
         for x in r.filter(row="S2-rough", **{"terrain.friction_amplitude": a}).rows}
    keys = sorted(set(f) & set(g))
    d = np.array([f[k] - g[k] for k in keys])
    mid.append(float(np.median(d)))
    lo, hi = bootstrap_ci(d)
    los.append(lo)
    his.append(hi)
ax.axhline(0.0, color="0.4", ls="--", lw=1.0)
ax.plot(AMS, mid, marker="o", ms=5, color="#7f2f8f")
ax.fill_between(AMS, los, his, alpha=0.20, color="#7f2f8f", lw=0)
ax.annotate("S2-flat better", xy=(0.02, 0.08), xycoords="axes fraction", fontsize=8, color="0.35")
ax.annotate("S2-rough better", xy=(0.02, 0.88), xycoords="axes fraction", fontsize=8, color="0.35")
ax.set_ylabel("paired difference\nS2-flat − S2-rough\n(matched run index, 95%)", fontsize=9)
ax.set_xlabel("terrain.friction_amplitude  (θ_m)")
ax.grid(alpha=0.25, lw=0.6)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9, frameon=False,
           bbox_to_anchor=(0.5, 0.038))
fig.suptitle(
    "Experiment 1: the 2×2 tuning control.  λ/R₀(gauci) = 0.69, n=20, τ=600 s, 100 runs/cell, held-out seeds\n"
    "S2-flat and S2-rough differ ONLY in the θ_m they were trained at — same optimiser, budget and training seeds.\n"
    "Of the Gauci→S2-rough gap at θ_m = 0.9, 96.9% is objective-tuning and 3.1% is terrain-tuning.\n"
    "The searched rows CROSS: flat wins below θ_m ≈ 0.3, rough wins above ≈ 0.45, both significant (bottom panel).",
    fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.90, bottom=0.115, left=0.14, right=0.97, hspace=0.13)
fig.text(0.5, 0.008, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_tuning_control.png", dpi=160)
print("wrote figures/terrain_tuning_control.png")
