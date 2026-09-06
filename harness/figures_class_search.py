"""Question B: does a transferring four-constant controller exist?

§14 showed the two single-condition searched rows failing to transfer — at 4× the
training start radius S2-rough forms a cluster in 34% of runs against Gauci's
100%, and at n = 50 both are worse than Gauci on flat ground everywhere. Nothing
had asked the optimiser to work anywhere but the arena it was given. This asks:
the same four constants, searched against the six-condition class the evaluation
grid is drawn from.

Three panel-rows — reach, absolute dispersion, time to first cluster — by two
panel-columns for θ_m. Start radius on the x axis, one line per row per n.
Dispersion is compared only within a cell; the cross-cell statistic is the paired
ratio against Gauci, which is in the section's tables rather than here.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import median_ci, wilson_ci

SUPTITLE = (
    "Question B: a class-searched controller fixes the swarm-size failure and not the start-radius one\n"
    "λ = 0.10 m, τ = 600 s, 100 runs/cell, held-out seeds.  Grey dashed vertical: the radius the single-condition rows were tuned at.\n"
    "S2-class-flat † beats Gauci in 9 of 12 cells, ties in 1 and loses 2 — both at 3.0 m under terrain, where reach is the binding constraint.\n"
    "At n = 50 on flat ground it is the only searched row that does not lose: 1.026, 1.016, 0.999 against the single-condition rows' 0.78–0.97.\n"
    "τ = 600 s truncates the 3.0 m column for EVERY row — Gauci reaches there in 46% of runs at 600 s and 100% at 3600 s — so §19's τ table, not this panel, decides that column."
)
r = load_jsonl("results/terrain_class_eval.jsonl")
ROWS = ["S2-gauci", "S2-flat", "S2-rough", "S2-class-flat", "S2-class-rough"]
ROWS = [row for row in ROWS if r.filter(row=row).rows]
RAD = r.unique("swarm.init.radius")
NS = r.unique("swarm.n")
AMS = r.unique("terrain.friction_amplitude")
colours = {
    "S2-gauci": "#ff7f0e", "S2-flat": "#1f77b4", "S2-rough": "#2ca02c",
    "S2-class-flat": "#9467bd", "S2-class-rough": "#d62728",
}
STYLE = {20: "-", 50: (0, (4, 2))}


def cell(row, a, rad, n):
    return r.filter(row=row, **{"terrain.friction_amplitude": a,
                                "swarm.init.radius": rad, "swarm.n": n})


def gather_time(sub):
    """Median time to first cluster among the runs that reached one.

    Runs that never reach have no time; scoring them as τ would invent a number
    and scoring them as missing hides them, so the count is printed with it.
    """
    ts = [x["time_to_first_single_cluster"] for x in sub.rows
          if x["ever_single_cluster"] and x["time_to_first_single_cluster"] is not None]
    return (median_ci(ts) if len(ts) >= 10 else (np.nan, np.nan, np.nan)), len(ts)


fig, axes = plt.subplots(3, len(AMS), figsize=(11.5, 11.0), sharex=True, squeeze=False)
handles: dict[str, object] = {}

for ci, a in enumerate(AMS):
    for row in ROWS:
        for n in NS:
            sub_any = r.filter(row=row, **{"swarm.n": n})
            name = f"{_label(row, sub_any)}, n = {n:g}"
            reach = [wilson_ci(cell(row, a, rad, n).column("ever_single_cluster")) for rad in RAD]
            disp = [median_ci(cell(row, a, rad, n).column("final_dispersion")) for rad in RAD]
            gt = [gather_time(cell(row, a, rad, n)) for rad in RAD]
            for ri, series in enumerate((reach, disp, [g[0] for g in gt])):
                m, lo, hi = zip(*series)
                line, = axes[ri][ci].plot(RAD, m, marker="o", ms=4, color=colours[row],
                                          ls=STYLE[n], label=name)
                axes[ri][ci].fill_between(RAD, lo, hi, alpha=0.12, color=colours[row], lw=0)
                if ri == 0:
                    handles.setdefault(name, line)
    axes[0][ci].set_title(f"θ_m = {a:g}", fontsize=10)
    for ri in range(3):
        axes[ri][ci].axvline(0.74, color="0.6", ls="--", lw=1.0, zorder=0)
        axes[ri][ci].grid(alpha=0.25, lw=0.6)
    axes[2][ci].set_xlabel("swarm.init.radius  (m)")

axes[0][0].set_ylabel("reach\n(Wilson 95%)", fontsize=9)
# A shared full-scale reach axis. Left to autoscale, the θ_m = 0 panel spans
# 0.963 to 1.000 and draws six flat lines that look like a result; on the same
# axis as the right panel it correctly reads "nothing happens here".
for ci in range(len(AMS)):
    axes[0][ci].set_ylim(0.0, 1.04)
axes[1][0].set_ylabel("final dispersion\n(absolute, median, 95%)\ncompare within a cell only", fontsize=9)
axes[2][0].set_ylabel("time to first cluster\n(s, median over runs that reached, 95%)", fontsize=9)
for ci in range(len(AMS)):
    axes[1][ci].set_yscale("log")
axes[0][0].annotate("the single-condition rows\nwere tuned here", xy=(0.74, 0.04),
                    xycoords=("data", "axes fraction"), xytext=(5, 0),
                    textcoords="offset points", fontsize=7.5, color="0.4")

fig.legend(list(handles.values()), list(handles.keys()), loc="lower center",
           ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.028))
fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.885, bottom=0.135, left=0.135, right=0.975, hspace=0.13, wspace=0.16)
fig.text(0.5, 0.006, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_class_search.png", dpi=160)
print("wrote figures/terrain_class_search.png")
