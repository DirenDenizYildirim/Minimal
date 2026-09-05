"""Experiment 3: does the terrain effect follow the controller down in λ?

Section 4 put the worst correlation length at λ/R₀ ≈ 0.7 for Gauci's
R₀ = 14.45 cm, and every terrain sweep since has run at that λ. S2-rough's R₀ is
4.74 cm, so if H2 is a statement about the controller's own turning circle its
worst λ is near 3.3 cm — which no sweep in this repository had visited.

Two panels of the same data. The left is λ in metres, which is what was swept;
the right is λ/R₀ with each row divided by **its own** R₀, which is the axis H2
is stated on. If H2 is controller-relative the two curves lie on top of each
other on the right and are displaced on the left.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import bootstrap_ci

SUPTITLE = "PLACEHOLDER"

r = load_jsonl("results/terrain_lambda_sweep.jsonl")
ROWS = ["S2-gauci", "S2-rough"]
LAMS = r.unique("terrain.correlation_length")
AMS = r.unique("terrain.friction_amplitude")
colours = {"S2-gauci": "#ff7f0e", "S2-rough": "#2ca02c"}

R0 = {}
for row in ROWS:
    values = {x["state0_turn_radius"] for x in r.filter(row=row).rows}
    assert len(values) == 1, (row, values)
    R0[row] = values.pop()

fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2), sharey=True)
summary = {}

for row in ROWS:
    mid, los, his = [], [], []
    for lam in LAMS:
        flat = {x["run_index"]: x["final_dispersion"]
                for x in r.filter(row=row, **{"terrain.correlation_length": lam,
                                              "terrain.friction_amplitude": min(AMS)}).rows}
        rough = {x["run_index"]: x["final_dispersion"]
                 for x in r.filter(row=row, **{"terrain.correlation_length": lam,
                                               "terrain.friction_amplitude": max(AMS)}).rows}
        keys = sorted(set(flat) & set(rough))
        d = np.array([rough[k] / flat[k] for k in keys])
        lo, hi = bootstrap_ci(d)
        mid.append(float(np.median(d)))
        los.append(lo)
        his.append(hi)
    summary[row] = (mid, los, his)
    label = _label(row, r.filter(row=row)) + f"  (R₀ = {R0[row] * 100:.2f} cm)"
    for ax, xs in ((axes[0], LAMS), (axes[1], [lam / R0[row] for lam in LAMS])):
        ax.plot(xs, mid, marker="o", ms=5, color=colours[row], label=label)
        ax.fill_between(xs, los, his, alpha=0.18, color=colours[row], lw=0)
    peak = int(np.argmax(mid))
    print(f"{row}: peak hold ratio {mid[peak]:.3f} [{los[peak]:.3f}, {his[peak]:.3f}] "
          f"at λ = {LAMS[peak] * 100:.2f} cm, λ/R₀ = {LAMS[peak] / R0[row]:.2f}")

axes[1].axvline(0.7, color="0.45", ls="--", lw=1.1)
axes[1].annotate("H2's predicted worst λ/R₀ ≈ 0.7", xy=(0.7, 0.97),
                 xycoords=("data", "axes fraction"), xytext=(5, 0),
                 textcoords="offset points", fontsize=8, color="0.35", va="top")
# The axle is fixed at 5.1 cm, so l/lambda = 1 is a single lambda, not a curve.
axes[0].axvline(0.051, color="#8a3b00", ls=":", lw=1.2)
axes[0].annotate("ℓ/λ = 1  (axle 5.1 cm)", xy=(0.051, 0.03), xycoords=("data", "axes fraction"),
                 xytext=(4, 0), textcoords="offset points", fontsize=8, color="#8a3b00")

for ax, xlabel in ((axes[0], "terrain.correlation_length  λ  (m)"),
                   (axes[1], "λ / R₀   (each row by its OWN R₀)")):
    ax.set_xscale("log")
    ax.axhline(1.0, color="0.5", ls=":", lw=1.0)
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.25, lw=0.6, which="both")
axes[0].set_ylabel("hold ratio\ndispersion at θ_m = 0.9 / own flat ground\n(paired by run index, median, 95%)",
                   fontsize=9)
axes[0].legend(fontsize=8.5, frameon=False)

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.80, bottom=0.155, left=0.115, right=0.98, wspace=0.06)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_lambda_sweep.png", dpi=160)
print("wrote figures/terrain_lambda_sweep.png")
