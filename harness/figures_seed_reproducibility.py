"""Phase 0: is the c*(θ) baseline a reproduced optimum or one draw?

S2-class-flat is the baseline and was found by one optimiser seed. Seeds 2 and 3
repeat the search under the identical protocol — same budget, same class, same
objective, same training seed base — so the spread between the three rows is the
optimiser's own variability and nothing else.

Four panels: what the searches returned, how the returned rows behave on the
held-out grid at both swarm sizes, and the gap between each search's reported
best objective and an honest re-score of the same constants.
"""

import itertools
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import median_ci

SUPTITLE = (
    "Phase 0: three identical searches, differing only in the optimiser seed — the baseline SCATTERS.\n"
    "sep-CMA-ES, 1200 × 12, six-condition class (radius × n), θ_m = 0, same training seed base 910 000; evaluated on §14's held-out grid.\n"
    "R₀ = 7.47, 8.88, 8.64 cm — a 16.9% spread, outside the pre-registered 10% rule — and 4 of 12 cells contain a disjoint pair of seeds.\n"
    "All three beat the enumerated reference almost everywhere (9/2/1, 10/0/2, 10/1/1 W/L/tied), and seed 1, the previous baseline, is the weakest.\n"
    "The baseline is therefore best-of-three † per cell, and this spread is its uncertainty."
)
AXLE, VMAX = 0.051, 0.128
SEEDS = ["S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3"]
ROWS = ["S2-gauci"] + SEEDS
FILES = {
    "S2-class-flat-s1": "results/search_s2_class_flat.json",
    "S2-class-flat-s2": "results/search_s2_class_flat_seed2.json",
    "S2-class-flat-s3": "results/search_s2_class_flat_seed3.json",
}
COLOURS = {"S2-gauci": "#ff7f0e", "S2-class-flat-s1": "#9467bd",
           "S2-class-flat-s2": "#1f77b4", "S2-class-flat-s3": "#2ca02c"}
STYLE = {0.0: (0, (4, 2)), 0.9: "-"}

C = {k: json.load(open(v))["best_constants"] for k, v in FILES.items()}
OBJ = {k: json.load(open(v))["best_training_objective"] for k, v in FILES.items()}
C["S2-gauci"] = [-0.7, -1.0, 1.0, -1.0]


def r0_of(c):
    v = 0.5 * (c[0] + c[1]) * VMAX
    w = (c[1] - c[0]) * VMAX / AXLE
    return abs(v / w) if abs(w) > 1e-12 else float("inf")


r = load_jsonl("results/phase0_seeds.jsonl")
RAD, NS, AMS = r.unique("swarm.init.radius"), r.unique("swarm.n"), r.unique("terrain.friction_amplitude")


def cell(row, a, rad, n):
    return r.filter(row=row, **{"terrain.friction_amplitude": a,
                                "swarm.init.radius": rad, "swarm.n": n})


fig, axes = plt.subplots(2, 2, figsize=(13.0, 10.0))

# --- A: what the searches returned -------------------------------------------
ax = axes[0][0]
labels = ["state-0 L", "state-0 R", "state-1 L", "state-1 R"]
for row in ROWS:
    ax.plot(range(4), C[row], marker="o", ms=7, color=COLOURS[row],
            ls="-" if row == "S2-gauci" else "-",
            lw=2.4 if row == "S2-gauci" else 1.6,
            label=f"{row}{'' if row == 'S2-gauci' else ' †'}  R₀ = {r0_of(C[row])*100:.2f} cm")
ax.set_xticks(range(4))
ax.set_xticklabels(labels)
ax.set_ylabel("wheel constant (fraction of 12.8 cm/s)", fontsize=9)
ax.set_ylim(-1.08, 1.08)
ax.axhline(0, color="0.7", lw=0.8)
ax.grid(alpha=0.25, lw=0.6)
ax.legend(fontsize=8, frameon=False, loc="center left")
r0v = [r0_of(C[s]) * 100 for s in SEEDS]
spread = 100 * (max(r0v) - min(r0v)) / np.mean(r0v)
ax.set_title(f"A. What three identical searches returned\n"
             f"R₀ = {', '.join(f'{v:.2f}' for v in r0v)} cm — spread {spread:.1f}% of the mean",
             fontsize=9.5)

# --- B, C: the held-out grid, one panel per n --------------------------------
for ax, n in zip((axes[0][1], axes[1][0]), NS):
    for row in ROWS:
        for a in AMS:
            m, lo, hi = zip(*[median_ci(cell(row, a, rad, n).column("final_dispersion"))
                              for rad in RAD])
            ax.plot(RAD, m, marker="o", ms=4, color=COLOURS[row], ls=STYLE[a],
                    label=f"{row}, θ_m = {a:g}" if n == NS[0] else None)
            ax.fill_between(RAD, lo, hi, alpha=0.12, color=COLOURS[row], lw=0)
    ax.set_yscale("log")
    ax.set_xlabel("swarm.init.radius  (m)")
    ax.set_ylabel("final dispersion (median, 95%)\ncompare within a cell only", fontsize=9)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_title(f"{'B' if n == NS[0] else 'C'}. Held-out grid, n = {n:g}, τ = 600 s\n"
                 f"(the 3.0 m θ_m = 0.9 column is truncated for every row)", fontsize=9.5)
axes[0][1].legend(fontsize=7.5, frameon=False, ncol=2, loc="upper left")

# --- D: the winner's-curse gap ------------------------------------------------
ax = axes[1][1]
try:
    p = load_jsonl("results/phase0_seeds_objective_probe.jsonl")
    conds = [(rad, n) for rad in p.unique("swarm.init.radius") for n in p.unique("swarm.n")]
    xs = np.arange(len(SEEDS))
    honest = []
    for s in SEEDS:
        meds = [float(np.median(np.asarray(
            p.filter(row=s, **{"swarm.init.radius": rad, "swarm.n": n}).column("final_dispersion"),
            dtype=float))) for rad, n in conds]
        honest.append(float(np.exp(np.mean(np.log(meds)))))
    rep = [OBJ[s] for s in SEEDS]
    ax.bar(xs - 0.19, rep, 0.36, color="0.72", label="reported best training objective\n(minimum of a noisy sample)")
    ax.bar(xs + 0.19, honest, 0.36, color=[COLOURS[s] for s in SEEDS],
           label="honest re-score, 100 runs/condition\non the same training seeds")
    for i, (a, b) in enumerate(zip(rep, honest)):
        ax.annotate(f"+{b-a:.3f}", xy=(i, max(a, b)), xytext=(0, 4),
                    textcoords="offset points", ha="center", fontsize=8.5, color="#8a3b00")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"seed {s[-1]}" for s in SEEDS])
    ax.set_ylabel("flat class objective\n(geometric mean of per-condition medians)", fontsize=9)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_title("D. The winner's-curse gap, measured for each seed", fontsize=9.5)
    ax.grid(alpha=0.25, lw=0.6, axis="y")
    print("honest re-scores:", {s: round(h, 4) for s, h in zip(SEEDS, honest)})
    print("reported:", {s: round(OBJ[s], 4) for s in SEEDS})
except FileNotFoundError:
    ax.text(0.5, 0.5, "objective probe not run", ha="center", transform=ax.transAxes)

print("L2 distances:", {f"{a[-2:]}-{b[-2:]}": round(math.dist(C[a], C[b]), 3)
                        for a, b in itertools.combinations(SEEDS, 2)})

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.865, bottom=0.065, left=0.085, right=0.98, hspace=0.30, wspace=0.24)
fig.text(0.5, 0.012, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/phase0_seed_reproducibility.png", dpi=160)
print("wrote figures/phase0_seed_reproducibility.png")
