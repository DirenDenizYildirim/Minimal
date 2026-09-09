"""§2 (Idea A, first grid): what terrain does to aggregation, on both dials.

Ported from two `swarm-figure` invocations whose arguments were never recorded
(verification-report D9). §10 describes them as "Gauci, α × θ_m grid" — a surface
and a curve — and that is what this script draws, from
`results/terrain_idea_a.jsonl`.

    figures_terrain_idea_a.py            both figures
    figures_terrain_idea_a.py surface    just the surface
    figures_terrain_idea_a.py curve      just the curve

THE RUNAWAY CORNER. At (15°, θ_m = 0.5) median dispersion is ~2656 — the swarm
spread over ~12 m — because `g_eff·sin α = 0.104 m/s` against a 0.128 m/s wheel
limit while traction reaches 1.5, so robots roll away downhill at different
rates. That is a real consequence of the model and the boundary of the usable
dial range, not a data point in a trend. On a shared linear colour scale it is
also the only thing visible: every other cell in the grid lies between 1.39 and
1.93. Both panels therefore work in log and the corner is called out in words,
which is the same treatment §2 gives it in prose.

The two dials are shown separately on purpose. §2's first result is that terrain
degrades cluster *quality* without stopping the swarm aggregating at all — reach
is 1.00 in every cell except the runaway corner, where it is 0.52 — and a
dispersion-only figure cannot say that.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE
from swarm_harness.stats import median_ci, wilson_ci

DEG = 180.0 / np.pi
r = load_jsonl("results/terrain_idea_a.jsonl")
SLOPES = r.unique("terrain.slope_angle")
AMPS = r.unique("terrain.friction_amplitude")
# Named so the caption and the annotation cannot drift apart.
RUNAWAY = (max(SLOPES), max(AMPS))

# The only row here is Gauci's enumerated controller, so neither stamp applies —
# saying "† searched, not exhaustive" on a tight minimum would be a false hedge.
PROVENANCE_NOTE = (UPPER_BOUND_NOTE if r.any_upper_bound() else
                   "The only row is Gauci's enumerated controller: a TIGHT minimum, not an upper bound.  "
                   "No †, no ‡.")
NOTE_COLOUR = "#8a3b00" if r.any_upper_bound() else "0.35"

PARAMS = ("M0-gauci (tight), g_eff = 0.4, λ = 0.15 m ≈ R₀, n = 20, τ = 600 s, "
          "start radius 0.74 m, 100 runs/cell")


def _grid(metric):
    z = np.full((len(AMPS), len(SLOPES)), np.nan)
    for i, a in enumerate(AMPS):
        for j, s in enumerate(SLOPES):
            cell = r.filter(**{"terrain.slope_angle": s, "terrain.friction_amplitude": a})
            if len(cell):
                z[i, j] = float(np.median(np.asarray(cell.column(metric), dtype=float)))
    return z


def surface():
    z = _grid("final_dispersion")
    reach = np.full_like(z, np.nan)
    for i, a in enumerate(AMPS):
        for j, s in enumerate(SLOPES):
            cell = r.filter(**{"terrain.slope_angle": s, "terrain.friction_amplitude": a})
            if len(cell):
                reach[i, j] = float(np.mean([1.0 if x else 0.0 for x in cell.column("ever_single_cluster")]))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0))
    xs = np.array([s * DEG for s in SLOPES])

    mesh = axes[0].pcolormesh(xs, AMPS, z, shading="nearest",
                              norm=LogNorm(vmin=np.nanmin(z), vmax=np.nanmax(z)), cmap="viridis")
    fig.colorbar(mesh, ax=axes[0], label="final dispersion (median, log scale)", fraction=0.046, pad=0.03)
    # Contours on the non-runaway part of the range only: a level between 2 and
    # 2656 would be a contour around one cell and say nothing.
    cs = axes[0].contour(xs, AMPS, z, levels=[1.5, 1.75, 2.0], colors="white", linewidths=1.3)
    axes[0].clabel(cs, fmt="%.2g", fontsize=8, colors="white")
    axes[0].set_title("median final dispersion", fontsize=10)

    mesh2 = axes[1].pcolormesh(xs, AMPS, reach, shading="nearest", vmin=0.0, vmax=1.0, cmap="magma")
    fig.colorbar(mesh2, ax=axes[1], label="reach: share of runs ever in one cluster", fraction=0.046, pad=0.03)
    axes[1].set_title("reach — 1.00 everywhere but the runaway corner", fontsize=10)

    for ax in axes:
        ax.set_xlabel("terrain.slope_angle  α  (degrees)")
        ax.set_ylabel("terrain.friction_amplitude  θ_m")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{v:g}" for v in xs])
        ax.set_yticks(AMPS)
        ax.plot([RUNAWAY[0] * DEG], [RUNAWAY[1]], marker="o", ms=16, mfc="none",
                mec="#ff3b00", mew=2.2, zorder=4)

    fig.suptitle(
        "§2, Idea A first grid: terrain degrades cluster QUALITY, it does not stop the swarm aggregating.\n"
        + PARAMS + "\n"
        f"Circled: the runaway corner (α = {RUNAWAY[0] * DEG:g}°, θ_m = {RUNAWAY[1]:g}), dispersion ≈{np.nanmax(z):.0f} "
        f"and reach {reach[AMPS.index(RUNAWAY[1]), SLOPES.index(RUNAWAY[0])]:.2f}.  There g_eff·sin α = 0.104 m/s against a\n"
        "0.128 m/s wheel limit and traction reaches 1.5, so robots roll away downhill: the boundary of the model's "
        "usable range, reported as such and NOT averaged into any trend.",
        fontsize=9, y=0.995, va="top",
    )
    fig.subplots_adjust(top=0.74, bottom=0.12, left=0.07, right=0.98, wspace=0.22)
    fig.text(0.5, 0.015, PROVENANCE_NOTE, ha="center", fontsize=7.5, style="italic", color=NOTE_COLOUR)
    fig.savefig("figures/terrain_idea_a_surface.png", dpi=160)
    print("wrote figures/terrain_idea_a_surface.png")


def curve():
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    cmap = plt.get_cmap("viridis")
    for i, s in enumerate(SLOPES):
        med, lo, hi = [], [], []
        for a in AMPS:
            m, l, h = median_ci(r.filter(**{"terrain.slope_angle": s,
                                            "terrain.friction_amplitude": a}).column("final_dispersion"))
            med.append(m); lo.append(l); hi.append(h)
        colour = cmap(i / max(1, len(SLOPES) - 1))
        ax.plot(AMPS, med, marker="o", ms=4.5, color=colour, label=f"α = {s * DEG:g}°")
        ax.fill_between(AMPS, lo, hi, alpha=0.16, color=colour, lw=0)
        print(f"α={s * DEG:5.1f}°  " + "  ".join(f"{m:.2f}" for m in med))

    ax.set_yscale("log")
    ax.axhline(1.43, color="0.5", ls=":", lw=1.0)
    ax.annotate("clean flat baseline 1.43", xy=(0.02, 1.43), xycoords=("axes fraction", "data"),
                xytext=(0, 4), textcoords="offset points", fontsize=8, color="0.35")
    ax.annotate(f"runaway corner:\nα = {RUNAWAY[0] * DEG:g}°, θ_m = {RUNAWAY[1]:g}",
                xy=(RUNAWAY[1], 2656), xytext=(-16, -6), textcoords="offset points",
                ha="right", fontsize=8, color="#ff3b00")
    ax.set_xlabel("terrain.friction_amplitude  θ_m")
    ax.set_ylabel("final dispersion, centroid frame\n(median, bootstrap 95%; log scale)", fontsize=9)
    ax.set_xticks(AMPS)
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(fontsize=8.5, frameon=False, title="slope", title_fontsize=8.5)

    fig.suptitle(
        "§2, Idea A first grid: monotone degradation on BOTH dials — H1 is not supported here.\n"
        + PARAMS + "\n"
        "The only hints in H1's direction (a small α or θ_m helping) sit inside run-to-run spread "
        "and did not survive the 200-runs/cell re-test in §3.",
        fontsize=9, y=0.995, va="top",
    )
    fig.subplots_adjust(top=0.79, bottom=0.11, left=0.115, right=0.98)
    fig.text(0.5, 0.015, PROVENANCE_NOTE, ha="center", fontsize=7.5, style="italic", color=NOTE_COLOUR)
    fig.savefig("figures/terrain_idea_a_curve.png", dpi=160)
    print("wrote figures/terrain_idea_a_curve.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["surface", "curve"]:
        globals()[name]()
