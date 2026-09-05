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

SUPTITLE = (
    "Experiment 3: the worst correlation length does NOT follow the controller.  θ_m = 0.9, n = 20, τ = 600 s,\n"
    "start radius 0.74 m, 100 runs/cell, λ log-spaced 2 → 20 cm.  Both rows peak at the same λ in METRES (7.46 cm),\n"
    "which is λ/R₀ = 0.52 for Gauci and λ/R₀ = 1.57 for S2-rough.  At S2-rough's own predicted worst λ (3.3 cm)\n"
    "its hold ratio is 1.05–1.09, near the bottom of its range.  H2 as an R₀-relative law is not supported here."
)

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

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
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
    axes[0].plot(LAMS, mid, marker="o", ms=5, color=colours[row], label=label)
    axes[0].fill_between(LAMS, los, his, alpha=0.18, color=colours[row], lw=0)
    # Right panel: excess over 1, scaled to each row's own peak. The two rows'
    # excesses differ twelvefold (Gauci 1.51, S2-rough 0.12), so on a shared
    # absolute axis the second curve is a flat line and the only question the
    # panel exists to answer — where is the peak — cannot be read off it. The
    # magnitudes are the left panel's job.
    peak_excess = max(m - 1.0 for m in mid)
    xs = [lam / R0[row] for lam in LAMS]
    axes[1].plot(xs, [(m - 1.0) / peak_excess for m in mid], marker="o", ms=5,
                 color=colours[row], label=label)
    axes[1].fill_between(xs, [(v - 1.0) / peak_excess for v in los],
                         [(v - 1.0) / peak_excess for v in his],
                         alpha=0.18, color=colours[row], lw=0)
    peak = int(np.argmax(mid))
    print(f"{row}: peak hold ratio {mid[peak]:.3f} [{los[peak]:.3f}, {his[peak]:.3f}] "
          f"at λ = {LAMS[peak] * 100:.2f} cm, λ/R₀ = {LAMS[peak] / R0[row]:.2f}")

axes[1].axvline(0.7, color="0.45", ls="--", lw=1.1)
axes[1].annotate("H2's predicted worst λ/R₀ ≈ 0.7", xy=(0.7, 0.28),
                 xycoords=("data", "axes fraction"), xytext=(5, 0),
                 textcoords="offset points", fontsize=8, color="0.35", va="top")
# The axle is fixed at 5.1 cm, so l/lambda = 1 is a single lambda, not a curve.
axes[0].axvline(0.051, color="#8a3b00", ls=":", lw=1.2)
axes[0].annotate("ℓ/λ = 1  (axle 5.1 cm)", xy=(0.051, 0.03), xycoords=("data", "axes fraction"),
                 xytext=(4, 0), textcoords="offset points", fontsize=8, color="#8a3b00")

from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter  # noqa: E402

for ax, xlabel, ticks in (
    (axes[0], "terrain.correlation_length  λ  (m)", [0.02, 0.05, 0.1, 0.2]),
    (axes[1], "λ / R₀   (each row by its OWN R₀)", [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]),
):
    ax.set_xscale("log")
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.25, lw=0.6)
    # Log minor ticks label themselves into an unreadable smear at this range.
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(ScalarFormatter())
axes[0].axhline(1.0, color="0.5", ls=":", lw=1.0)
axes[1].axhline(0.0, color="0.5", ls=":", lw=1.0)
axes[0].set_ylabel("hold ratio\ndispersion at θ_m = 0.9 / own flat ground\n(paired by run index, median, 95%)",
                   fontsize=9)
axes[1].set_ylabel("excess hold ratio, scaled to each row's own peak\n"
                   "(1.0 = that row's worst λ; magnitudes on the left panel)", fontsize=9)
axes[0].legend(fontsize=8.5, frameon=False)

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.795, bottom=0.15, left=0.095, right=0.985, wspace=0.30)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_lambda_sweep.png", dpi=160)
print("wrote figures/terrain_lambda_sweep.png")
