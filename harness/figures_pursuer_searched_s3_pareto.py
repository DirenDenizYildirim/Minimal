"""Experiment 1's Pareto figure: all FOUR kinds of row on one pair of axes.

Pre-registered at docs/preregistration/searched-s3-pursuer.md (577f15a); the
four-kinds requirement is pseudo-reality.md's deviation D2.

`figures_pareto.py` draws §12's figure from `pursuer_pareto.jsonl` and is left
alone. This one exists because §12's figure has only two kinds of row on it —
hand-designed aggregating and hand-designed dispersive — and the trade-off it
shows could therefore be an artefact of two hand-designed corners. Adding the
searched rows is what turns "these two guesses trade off" into "a search that was
told to maximise survival alone walks to the dispersive corner on its own, from a
B1-ternary start".

  hand-designed aggregating   B0-blind (enumerated), B1-ternary ‡
  hand-designed dispersive    D-dispersive ‡
  searched, two-axis          S3-survival_task-s1..s3 †   (survival AND task)
  searched, survival-only     S3-survival-s1..s3 †        (survival ALONE)

SURVIVAL IS MEAN PER-ROBOT WITH A WILSON INTERVAL (§12.1 D0), not a median of
`survival_fraction`. §12's figure predates D0 and uses the retired statistic; the
two are not interchangeable and this figure does not mix them.

THE ≤ 5-SURVIVOR CAVEAT, and its denominator. A dispersion "among survivors" is
computed only on runs with at least MIN_SURVIVORS, so the share that matters is
the share OF THOSE RUNS with barely more than the minimum. Both numbers are drawn
on the figure per row, because they differ by row and the reader cannot otherwise
tell which points rest on nearly-intact swarms and which on a handful of robots.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE
from swarm_harness.stats import median_ci, wilson_ci

R_START = 0.74     # metres — the disc the swarm starts inside; r_p is read in these
MIN_SURVIVORS = 3  # below this, "dispersion among survivors" is degenerate

KINDS = {
    "hand-designed, aggregating": (["B0-blind", "B1-ternary"], "#1f77b4", "s"),
    "hand-designed, dispersive":  (["D-dispersive"], "#d62728", "D"),
    "searched †, two-axis (survival AND task)":
        (["S3-survival_task-s1", "S3-survival_task-s2", "S3-survival_task-s3"], "#2ca02c", "o"),
    "searched †, survival-only":
        (["S3-survival-s1", "S3-survival-s2", "S3-survival-s3"], "#9467bd", "^"),
}
ROWS = [r for rows, _c, _m in KINDS.values() for r in rows]

r = load_jsonl("results/pursuer_searched_s3_pareto.jsonl")
RP = r.unique("pursuer.range")
KS = r.unique("pursuer.confusion")


def per_robot(rows):
    flags = []
    for x in rows:
        n, s = int(x["n"]), int(x["survivors"])
        flags.extend([1.0] * s + [0.0] * (n - s))
    return wilson_ci(flags)


def mark(row):
    return r.filter(row=row).mark()


fig, axes = plt.subplots(len(KS), len(RP), figsize=(15.0, 9.4), sharey=True)

for row_i, k in enumerate(KS):
    for col_i, rp in enumerate(RP):
        ax = axes[row_i][col_i]
        # Stacked, because in the perfect-perception column four rows are
        # unestimable at once and one anchor point would print them on top of
        # each other.
        unestimable = 0
        for kind, (rows, colour, marker) in KINDS.items():
            for j, row in enumerate(rows):
                cell = r.filter(row=row, **{"pursuer.range": rp, "pursuer.confusion": k})
                if not cell.rows:
                    continue
                s, slo, shi = per_robot(cell.rows)
                ok = [x["final_dispersion"] for x in cell.rows
                      if x["survivors"] >= MIN_SURVIVORS]
                if len(ok) < 10:
                    ax.annotate(f"{row}{mark(row)}: task not estimable "
                                f"({len(ok)}/{len(cell.rows)} runs ≥ {MIN_SURVIVORS} survivors)",
                                # x = 0.25 puts these in the empty decade between
                                # the aggregating cluster (~1 m) and D (~400 m),
                                # which is clear in all six panels; anchoring at
                                # the left edge lands them on the low-survival
                                # points in the perfect-perception column.
                                xy=(0.25, 0.105 + 0.055 * unestimable),
                                xycoords="axes fraction", fontsize=6.4, color=colour)
                    unestimable += 1
                    continue
                d, dlo, dhi = median_ci(ok)
                ax.errorbar([d], [s], xerr=[[d - dlo], [dhi - d]],
                            yerr=[[s - slo], [shi - s]], fmt=marker,
                            ms=9 - 1.2 * j, color=colour,
                            markerfacecolor=colour if j == 0 else "none",
                            markeredgewidth=1.6, capsize=2.5, elinewidth=1.0, zorder=3,
                            label=kind if (row_i == 0 and col_i == 0 and j == 0) else None)
        ax.set_xscale("log")
        ax.set_xlim(0.7, 6e4)
        ax.grid(alpha=0.25, lw=0.6)
        corner = "  — perfect perception" if rp >= R_START else ""
        ax.set_title(f"r_p = {rp:g} m = {rp / R_START:.2f} R,  κ = {k:g}{corner}",
                     fontsize=9.5, color="#8a3b00" if rp >= R_START else "black")
        if row_i == len(KS) - 1:
            ax.set_xlabel("base task among survivors\nfinal dispersion, m (lower better, log)",
                          fontsize=8.5)
        if col_i == 0:
            ax.set_ylabel("mean per-robot survival at τ\n(Wilson 95%)", fontsize=8.5)

# ---- the survivor caveat, per row, on the figure rather than in prose ---------
lines = []
for kind, (rows, _c, _m) in KINDS.items():
    for row in rows:
        allr = r.filter(row=row).rows
        usable = [x for x in allr if x["survivors"] >= MIN_SURVIVORS]
        le5 = sum(1 for x in usable if x["survivors"] <= 5)
        lines.append(f"{row}{mark(row)}: {len(usable)}/{len(allr)} runs usable, "
                     f"{100 * le5 / len(usable):.1f}% of those with ≤ 5 survivors"
                     if usable else f"{row}: no usable runs")
handles, labels = axes[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8.4, frameon=False,
           bbox_to_anchor=(0.5, 0.128))

fig.text(0.5, 0.098, "runs the dispersion rests on, over these six cells:",
         ha="center", fontsize=7.6, color="0.25", style="italic")
for i, line in enumerate(lines):
    fig.text(0.055 + 0.317 * (i % 3), 0.078 - 0.019 * (i // 3), line,
             ha="left", fontsize=6.6, color="0.3")

fig.suptitle(
    "Experiment 1: the survival/task trade-off with ALL FOUR kinds of row.  "
    "ρ = 1.5, h = 1.93 s, n = 20, τ = 120 s, R = 0.74 m, 100 runs/cell, held-out seeds.\n"
    "The searched survival-only rows † — told to maximise survival ALONE, started at B1-ternary's own "
    "constants — walk to the dispersive corner by themselves. The trade-off is not an artefact of one "
    "hand-designed guess.\n"
    "Those rows are NOT almost-dead swarms with two robots far apart: every run usable, never fewer than "
    "nine survivors, dispersion of ~10 000 m. They are nearly-intact swarms spread over hundreds of metres.\n"
    "The ≤ 5-survivor caveat belongs to D-dispersive ‡ and B1-ternary ‡ — and equally to the two-axis "
    "searched rows †, which carry it at the same magnitude. Per-row figures below the panels.",
    fontsize=8.6, y=0.995, va="top")
fig.subplots_adjust(top=0.845, bottom=0.235, left=0.062, right=0.985, hspace=0.34, wspace=0.08)
fig.text(0.5, 0.012, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/pursuer_searched_s3_pareto.png", dpi=160)
print("wrote figures/pursuer_searched_s3_pareto.png")
