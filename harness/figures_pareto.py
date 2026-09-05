"""Idea B Pareto front: survival against base-task performance among survivors.

Every earlier Idea B figure scored survival alone, which cannot see what
surviving cost. A row that abandons aggregation to stay alive is not a better
controller; it is the other end of a trade-off, and that only becomes visible
with both coordinates on the same plot.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE
from swarm_harness.stats import median_ci

ROWS = ["B0-blind", "B1-ternary", "B2-ternary-side", "B3-ternary-memory", "D-dispersive"]
CELLS = [(0.2, 0.0), (0.35, 3.0), (1.0, 3.0)]
# Below three survivors the dispersion of "the survivors" is degenerate: one or
# zero survivors scores 0, which is a perfect aggregation score for a swarm that
# has been wiped out.
MIN_SURVIVORS = 3

r = load_jsonl("results/pursuer_pareto.jsonl")
MARK = {}
for row in ROWS:
    MARK[row] = r.filter(row=row).mark()

fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.0), sharey=True)
colours = plt.rcParams["axes.prop_cycle"].by_key()["color"]

for ax, (rp, k) in zip(axes, CELLS):
    unestimable: list[str] = []
    placed: list[tuple[float, float]] = []
    for i, row in enumerate(ROWS):
        cell = r.filter(row=row, **{"pursuer.range": rp, "pursuer.confusion": k})
        surv = median_ci(cell.column("survival_fraction"))
        ok = [x for x in cell.rows if x["survivors"] >= MIN_SURVIVORS]
        is_end = row.startswith("D-")
        if len(ok) < 10:
            # Not estimable: say so on the panel rather than plotting a point
            # whose interval is an artefact of one or two runs.
            # Anchored top-left: the plotted points in these cells sit low and
            # to the left, and an annotation there would land on them.
            ax.annotate(
                f"{row}{MARK[row]}: base task not estimable "
                f"({len(ok)}/100 runs had ≥{MIN_SURVIVORS} survivors)",
                xy=(0.03, 0.97 - 0.07 * len(unestimable)),
                xycoords="axes fraction", va="top",
                fontsize=6.8,
                color=colours[i % len(colours)],
            )
            unestimable.append(row)
            continue
        disp = median_ci([x["final_dispersion"] for x in ok])
        ax.errorbar(
            [disp[0]], [surv[0]],
            xerr=[[disp[0] - disp[1]], [disp[2] - disp[0]]],
            yerr=[[surv[0] - surv[1]], [surv[2] - surv[0]]],
            fmt="D" if is_end else "o",
            markersize=11 if is_end else 8,
            color=colours[i % len(colours)],
            markerfacecolor="none" if is_end else colours[i % len(colours)],
            markeredgewidth=2.0 if is_end else 1.0,
            capsize=3, elinewidth=1.2, zorder=3,
            label=f"{row}{MARK[row]}" + ("  — task-abandoning end" if is_end else ""),
        )
        # Stagger labels for points that land almost on top of each other.
        crowd = sum(1 for px, py in placed
                    if abs(np.log10(px) - np.log10(disp[0])) < 0.12 and abs(py - surv[0]) < 0.10)
        ax.annotate(row.split("-")[0] + MARK[row], (disp[0], surv[0]),
                    textcoords="offset points", xytext=(9, 6 - 11 * crowd), fontsize=8,
                    color=colours[i % len(colours)])
        placed.append((disp[0], surv[0]))
    ax.set_xscale("log")
    ax.set_xlim(right=ax.get_xlim()[1] * 2.2)  # room for the right-hand label
    ax.set_xlabel("base task among survivors\nfinal dispersion, centroid frame (lower better)")
    ax.set_title(f"r_p = {rp} m,  κ = {k:g}", fontsize=10)
    ax.grid(alpha=0.25, lw=0.6)
axes[0].set_ylabel("survival fraction at τ\n(median, bootstrap 95%)")

handles, labels = axes[0].get_legend_handles_labels()
for ax in axes[1:]:
    for h, l in zip(*ax.get_legend_handles_labels()):
        if l not in labels:
            handles.append(h)
            labels.append(l)
order = sorted(range(len(labels)), key=lambda i: ROWS.index(labels[i].split(" ")[0].rstrip("†‡")))
fig.legend([handles[i] for i in order], [labels[i] for i in order],
           loc="lower center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.055))

fig.suptitle(
    "Experiment 4: Idea B Pareto front — survival bought with the base task\n"
    "D-dispersive is the TASK-ABANDONING END OF THE FRONT, not a competitor controller: it survives by "
    "giving up aggregation entirely (dispersion ~400, two orders above the others).\n"
    "At r_p = 0.35, κ = 3 there is no trade-off at all — the aggregating rows beat it on BOTH axes. "
    "At the other two cells the trade-off is real.",
    fontsize=9, y=0.985, va="top",
)
fig.text(0.5, 0.845, "ρ = 1.5   h = 1.93 s   n = 20   τ = 120 s   start radius = 0.74 m   100 runs/cell",
         ha="center", fontsize=8, color="0.3")
fig.subplots_adjust(top=0.74, bottom=0.29, wspace=0.12)
fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/pursuer_pareto.png", dpi=160)
print("wrote figures/pursuer_pareto.png")
