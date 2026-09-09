"""§1 (week-3 shakedown): occlusion, nominal rate against realised rate.

Ported from two `swarm-figure` invocations whose arguments were never recorded
(verification-report D9). §10 describes them as "M0 tight, M1 ‡, FN rate ×
correlation" — a curve and a surface over that grid — and that is what this
script draws, from `results/occlusion_shakedown.jsonl`.

    figures_occlusion_shakedown.py            both figures
    figures_occlusion_shakedown.py curve      just the curve
    figures_occlusion_shakedown.py surface    just the surface

The curve gets a second panel the original did not have, because the result that
survived from this section is a statement the first panel cannot make. At matched
*nominal* rate the correlated dropout looks dramatically worse than i.i.d., but
the realised rate at a nominal 0.6 is 0.89: the swarm ends up where the field is
blind, so the two conditions are not being compared at the same dropout at all.
Binned by *realised* rate, the extra penalty for spatial structure appears only
above ≈0.8. The standing rule this produced — compare spatially varying dials at
matched **realised** intensity — is why `realised_fn_rate` is on every record,
and a figure that plots only the nominal axis invites exactly the reading the
section retracted.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness import plot
from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import median_ci

CORR_FIELD = "occlusion.correlation_amplitude"
ROWS = ["M0-gauci", "M1-hysteresis"]
# Realised-rate bins, as §1 reports them.
BINS = [(0.00, 0.05), (0.25, 0.35), (0.45, 0.55), (0.60, 0.70),
        (0.72, 0.80), (0.85, 0.95), (0.95, 1.00)]
COLOURS = {("M0-gauci", 0.0): "#1f77b4", ("M0-gauci", 0.9): "#d62728",
           ("M1-hysteresis", 0.0): "#7fb3d5", ("M1-hysteresis", 0.9): "#e8908f"}

r = load_jsonl("results/occlusion_shakedown.jsonl")
CORRS = r.unique(CORR_FIELD)


def curve():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
    fns = r.unique("occlusion.fn_rate")

    for row in ROWS:
        for c in CORRS:
            sub = r.filter(row=row, **{CORR_FIELD: c})
            med, lo, hi = [], [], []
            for fn in fns:
                m, l, h = median_ci(sub.filter(**{"occlusion.fn_rate": fn}).column("final_dispersion"))
                med.append(m); lo.append(l); hi.append(h)
            style = "-" if c == 0.0 else "--"
            label = f"{_label(row, sub)}, {'i.i.d.' if c == 0.0 else f'correlated (amp {c:g})'}"
            colour = COLOURS.get((row, c), None)
            axes[0].plot(fns, med, marker="o", ms=4, ls=style, color=colour, label=label)
            axes[0].fill_between(fns, lo, hi, alpha=0.15, color=colour, lw=0)

    # Right panel: the same runs, binned by the dropout each run actually saw.
    for row in ROWS:
        for c in CORRS:
            sub = r.filter(row=row, **{CORR_FIELD: c})
            xs, med, lo, hi = [], [], [], []
            for a, b in BINS:
                vals = [x["final_dispersion"] for x in sub.rows if a <= x["realised_fn_rate"] <= b]
                if len(vals) < 20:      # too few runs landed in this bin to estimate
                    continue
                m, l, h = median_ci(vals)
                xs.append(0.5 * (a + b)); med.append(m); lo.append(l); hi.append(h)
            style = "-" if c == 0.0 else "--"
            colour = COLOURS.get((row, c), None)
            axes[1].plot(xs, med, marker="s", ms=4, ls=style, color=colour)
            axes[1].fill_between(xs, lo, hi, alpha=0.15, color=colour, lw=0)

    axes[1].axvline(0.8, color="#8a3b00", ls=":", lw=1.2)
    axes[1].annotate("above ≈0.8 realised, spatial structure\ncosts something extra",
                     xy=(0.8, 0.97), xycoords=("data", "axes fraction"),
                     xytext=(-4, 0), textcoords="offset points",
                     ha="right", va="top", fontsize=8, color="#8a3b00")

    for ax, xlabel in ((axes[0], "occlusion.fn_rate   (NOMINAL false-negative rate)"),
                       (axes[1], "realised false-negative rate   (what the swarm actually saw)")):
        ax.set_xlabel(xlabel)
        ax.set_yscale("log")
        ax.grid(alpha=0.25, lw=0.6)
        ax.axhline(1.43, color="0.5", ls=":", lw=1.0)
    axes[0].annotate("clean-arena baseline 1.43", xy=(0.02, 1.43),
                     xycoords=("axes fraction", "data"), xytext=(0, 4),
                     textcoords="offset points", fontsize=8, color="0.35")
    axes[0].set_ylabel("final dispersion, centroid frame\n(median, bootstrap 95%; log scale)", fontsize=9)
    axes[0].legend(fontsize=8, frameon=False, loc="upper left")

    fig.suptitle(
        "§1 shakedown: occlusion.  n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell, clean baseline 1.43.\n"
        "LEFT, nominal rate: correlated dropout looks far worse than i.i.d. — but at a nominal 0.6 the REALISED\n"
        "rate is 0.89, so the two conditions are not being compared at the same dropout.  RIGHT, matched on the\n"
        "realised rate: below ≈0.8 the two are within each other's spread; the extra penalty is real only above it.",
        fontsize=9, y=0.995, va="top",
    )
    fig.subplots_adjust(top=0.835, bottom=0.12, left=0.085, right=0.985, wspace=0.22)
    fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
    fig.savefig("figures/occlusion_shakedown_curve.png", dpi=160)
    print("wrote figures/occlusion_shakedown_curve.png")


def surface():
    fig = plot.surface(
        r,
        x="occlusion.fn_rate",
        y=CORR_FIELD,
        metric="final_dispersion",
        thresholds=[2.0, 3.0, 4.0],
        # The correlated corner reaches ~39 and would leave the whole low half of
        # the grid one flat colour. The scale stops at 5 and that corner
        # saturates; contours are computed per panel from the unclipped values.
        vmin=1.4,
        vmax=5.0,
        title="§1 shakedown: median final dispersion over (nominal FN rate, spatial correlation).\n"
        "n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell.  Clean-arena baseline is 1.43.\n"
        "The correlation axis has two values by design (i.i.d. and amplitude 0.9); the honest comparison "
        "between them is at matched REALISED rate, in the curve figure's right panel, not on this axis.",
        annotate=["n", "duration", "start_radius"],
    )
    # `plot.surface` uses one wspace for every panel count, and the dotted-path y
    # label of the second panel lands inside the first. Widening the gap moves
    # the panels but not the colorbar, which `fig.colorbar` placed already, so
    # the colorbar is re-seated by hand afterwards. Local to this figure, so
    # nothing else in the inventory moves.
    fig.subplots_adjust(wspace=0.30, right=0.86)
    box = fig.axes[0].get_position()
    fig.axes[-1].set_position([0.885, box.y0, 0.016, box.height])
    fig.savefig("figures/occlusion_shakedown_surface.png", dpi=160, bbox_inches="tight")
    print("wrote figures/occlusion_shakedown_surface.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["curve", "surface"]:
        globals()[name]()
