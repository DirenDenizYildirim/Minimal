"""§9: does re-tuning move the problem or solve it?  And §10: the warm-started S = 4.

Ported from two `swarm-figure` invocations whose arguments were never recorded
(verification-report D9). §10 of the source describes them as "four rows incl.
S4-composite ‡" (§9) and "S2-searched †, S4 cold †, S4-warm †" (§10), and that is
what this script draws.

    figures_terrain_retune_cost.py            both figures
    figures_terrain_retune_cost.py retune     just terrain_retune_cost.png
    figures_terrain_retune_cost.py warm       just terrain_warm_s4.png

`terrain_warm_s4.toml` says its grid is identical to `terrain_retune_cost.toml`
and run under the same base seeds so the rows are directly comparable, so the
warm figure reads both files and plots them on one axis. That is the only reason
the two live in one script.

ABSOLUTE DISPERSION, NOT A HOLD RATIO. §7's figure normalises each row by its own
flat ground, which is right there because the question is terrain robustness.
Here the question is what re-tuning *costs elsewhere*, and the answer — that
S2-searched is 12.2% better than Gauci on ground it was never tuned for — is
invisible in a ratio, which pins every row to 1.0 at θ_m = 0 by construction.

S4-COMPOSITE IS A CONSTRUCTIVE DEMONSTRATION, NOT A CANDIDATE. It is a
hand-built switch (bit 0 → Gauci, bit 1 → S2-searched) and it is worse than the
S = 2 row it is built from at every θ_m, because half the time it deliberately
selects the worse of its two behaviours. Its θ_m = 0 value reproducing Gauci's
exactly is the internal consistency check: on flat ground the bit is never set,
so the composite *is* Gauci.

NOT A BYTE-FOR-BYTE PORT, and it cannot be one. The image this replaces was drawn
by a `swarm-figure` invocation whose arguments were never recorded, so there is
no committed original to compare against and no way to tell whether any
reconstruction is the same figure — the one attempt made during the verification
pass differed from the committed PNG in 44% of pixels. What this script
reproduces is the figure `paper-source.md` §10 *describes*. Written 2026-09-10,
in the freeze-lift-1 Phase 0 regeneration; nobody should read a later diff
against the lost image as a regression.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from swarm_harness.load import Records, load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import median_ci, wilson_ci

AMP = "terrain.friction_amplitude"
COLOURS = {"S2-gauci": "#1f77b4", "S2-searched": "#2ca02c", "S4-composite": "#9467bd",
           "S4-searched": "#d62728", "S4-warm": "#ff7f0e"}

retune_records = load_jsonl("results/terrain_retune_cost.jsonl")


def _panel(ax, records, rows, metric, summarise, note=None):
    amps = records.unique(AMP)
    for row in rows:
        sub = records.filter(row=row)
        med, lo, hi = [], [], []
        for a in amps:
            vals = sub.filter(**{AMP: a}).column(metric)
            if metric == "ever_single_cluster":
                vals = [1.0 if v else 0.0 for v in vals]
            m, l, h = summarise(vals)
            med.append(m); lo.append(l); hi.append(h)
        ax.plot(amps, med, marker="o", ms=4.5, color=COLOURS[row], label=_label(row, sub))
        ax.fill_between(amps, lo, hi, alpha=0.16, color=COLOURS[row], lw=0)
        print(f"  {row:14s} " + "  ".join(f"{m:.3f}" for m in med))
    ax.set_xlabel("terrain.friction_amplitude  θ_m")
    ax.set_xticks(amps)
    ax.grid(alpha=0.25, lw=0.6)
    if note:
        ax.set_title(note, fontsize=9.5)


def retune():
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.4))
    rows = ["S2-gauci", "S2-searched", "S4-composite", "S4-searched"]
    print("terrain_retune_cost: median final dispersion")
    _panel(axes[0], retune_records, rows, "final_dispersion", median_ci,
           "final dispersion (median, bootstrap 95%) — disjoint at every one of the eight θ_m")
    print("terrain_retune_cost: reach")
    _panel(axes[1], retune_records, rows, "ever_single_cluster", wilson_ci,
           "reach: share of runs ever in one cluster (Wilson 95%)")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("final dispersion, centroid frame  (log scale)", fontsize=9)
    axes[1].set_ylabel("reach", fontsize=9)
    axes[1].set_ylim(0.0, 1.05)
    axes[0].legend(fontsize=8.5, frameon=False)

    fig.suptitle(
        "§9: re-tuning the same four constants does not move the problem elsewhere — it is better on flat ground too.\n"
        "λ = 0.10 m fixed, θ_m 0 → 0.9 in eight steps, n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell.\n"
        "Pre-registered rule anticipated two branches at θ_m = 0 (S2-searched matches Gauci within CI, or is disjointly\n"
        "worse).  NEITHER fired: it is strictly BETTER, 1.253 [1.234, 1.283] against 1.427 [1.399, 1.467], 12.2% lower,\n"
        "on ground it was never tuned for.  S4-composite ‡ is a hand-built switch, worse than the S = 2 row it is built\n"
        "from at every θ_m; its θ_m = 0 value reproduces Gauci's exactly, which is the consistency check.\n"
        "SUPERSEDED IN ITS EXPLANATION by §13/§14: 're-tuning solves it' was right about the direction, wrong about the\n"
        "cause — most of the gap is objective-tuning, not terrain-tuning.  The flatness in CAPABILITY stands.",
        fontsize=9, y=0.995, va="top",
    )
    fig.subplots_adjust(top=0.68, bottom=0.12, left=0.075, right=0.985, wspace=0.20)
    fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
    fig.savefig("figures/terrain_retune_cost.png", dpi=160)
    print("wrote figures/terrain_retune_cost.png")


def warm():
    # Same grid, same base seeds, so the two files are one figure.
    merged = Records(retune_records.rows + load_jsonl("results/terrain_warm_s4.jsonl").rows)
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    print("terrain_warm_s4: median final dispersion")
    _panel(ax, merged, ["S2-searched", "S4-searched", "S4-warm"], "final_dispersion", median_ci)
    ax.set_ylabel("final dispersion, centroid frame\n(median, bootstrap 95%)", fontsize=9)
    ax.legend(fontsize=8.5, frameon=False)

    fig.suptitle(
        "§10: given the S = 2 optimum as a starting point and equal budget, USING the terrain bit did not beat IGNORING it.\n"
        "The warm search began at [S2-searched | S2-searched] — an eight-constant table whose halves are equal, i.e. an\n"
        "S = 4 controller that ignores its own bit — so the only question it can be asked is whether using the bit helps.\n"
        "It did move (L2 0.464 from its start, halves diverging by up to 0.254), so the found controller genuinely uses it.\n"
        "At the peak (θ_m = 0.9) the intervals OVERLAP and the point estimate is 2.1% worse: 1.412 [1.349, 1.503] against\n"
        "1.383 [1.350, 1.441].  The warm start does beat the cold S = 4 search (1.486), which is what a better start should do.\n"
        "The winner's curse, shown: warm training objective 1.2595 beat cold 1.3012 and S = 2's 1.3009.  On held-out seeds\n"
        "that advantage disappears entirely.  Same optimiser, same budget (600 × 12); training seeds 950 000, disjoint.\n"
        "λ = 0.10 m, n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell.",
        fontsize=9, y=0.995, va="top",
    )
    fig.subplots_adjust(top=0.60, bottom=0.11, left=0.11, right=0.98)
    fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
    fig.savefig("figures/terrain_warm_s4.png", dpi=160)
    print("wrote figures/terrain_warm_s4.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["retune", "warm"]:
        globals()[name]()
