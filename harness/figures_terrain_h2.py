"""§4 (Idea A, H2): does the terrain transition scale with R₀, or with the axle?

Ported from two `swarm-figure surface` invocations whose arguments were never
recorded (verification-report D9); the reconstruction attempted in the
verification pass differed from the committed `terrain_h2_powered.png` in 44% of
pixels, so nothing was checkable. §10 describes the two as "four R₀ rows" (the
first pass) and "five rows breaking the R₀/axle confound, θ_m to 1.0" (the
powered sweep), both `--baseline-y`, and that is what this script draws.

    figures_terrain_h2.py            both figures
    figures_terrain_h2.py powered    just terrain_h2_powered.png
    figures_terrain_h2.py r0_scaling just terrain_h2_r0_scaling.png

WHY `--baseline-y` IS NOT COSMETIC. The five rows differ from each other on flat
ground — forward speed 9.5–11.8 cm/s, turn rate 0.41–1.31 rad/s — because each
one varies the wheel constants or the axle to hold one length scale fixed. On a
shared raw colour scale the largest-R₀ row swamps every panel while saying
nothing about terrain. Each column is therefore divided by its own θ_m = 0 cell
at the same λ, so what is plotted is degradation relative to that row's own
baseline. That is also how §4's table is computed.

WHY THE POWERED FIGURE STOPS AT θ_m = 1.0. The sweep runs to 1.5, where the
traction multiplier clamps at the floor and wheels stall outright: every row
degrades 6–14× and the ordering by R₀ collapses. That band is stall, not terrain
(correction #10), so the figure is drawn from `terrain_h2_powered_valid.jsonl`,
the θ_m ≤ 1.0 subset. `scripts/regenerate_record.sh` records the filter.

WHAT THIS FIGURE STILL SUPPORTS, AND WHAT IT NO LONGER DOES. §15 and §17 show the
peak is *not* proportional to R₀ once R₀ is varied inside one controller family
on a finer λ grid, and §18 identifies the length as the body diameter. What
survives here is the R₀-versus-axle comparison: at θ_m = 1.0 a 4× change of axle
at fixed R₀ moves the peak degradation by 5%, a 4× change of R₀ at fixed axle by
560%. The caption says so, because a reader who takes this panel for a ratio law
is taking a superseded reading.

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

from swarm_harness import plot
from swarm_harness.load import load_jsonl

# `plot.surface` reserves a fixed fraction of the width for the colorbar, which
# at five panels leaves its label off the canvas. Saving with a tight bounding
# box grows the canvas to fit instead of cropping the label, and changes nothing
# else about the figure -- so the fix stays here rather than in the shared
# plotting code every other figure also uses.
def save_tight(fig, out):
    fig.savefig(out, dpi=160, bbox_inches="tight")
    print(f"wrote {out}")

# `axle-x2-R0-same` puts the wheel contacts outside the 7.4 cm body. It is a
# numerical device for separating two length scales, not a buildable robot, and
# it is also the row that makes the 5% spread meaningful — so it stays in,
# labelled, in the caption as well as in the text.
NOT_BUILDABLE = ("axle-x2-R0-same ‡ has its wheel contacts OUTSIDE the 7.4 cm body: "
                 "a numerical device to separate λ/R₀ from λ/axle, not a robot that can be built.")


def powered():
    r = load_jsonl("results/terrain_h2_powered_valid.jsonl")
    fig = plot.surface(
        r,
        x="terrain.correlation_length",
        y="terrain.friction_amplitude",
        metric="final_dispersion",
        baseline_y=0.0,
        thresholds=[1.5, 2.0, 3.0],
        # The R0-x2 row reaches 10.46 at the peak. On a shared scale reaching
        # that, the other four panels are one flat colour and the figure says
        # only "one row is much worse", which the caption can say in words. The
        # colour scale therefore stops at 3.0 and that row saturates; the
        # contours are computed per panel from the unclipped values, so the
        # T = 3 line still sits where it belongs.
        vmin=1.0,
        vmax=3.0,
        title="§4, H2 powered: the transition tracks R₀, not the axle.  Five rows holding one length scale fixed while\n"
        "varying the other; each column divided by its OWN θ_m = 0 cell at the same λ.  n = 20, τ = 600 s, start radius\n"
        "0.74 m, slope 0, 100 runs/cell, θ_m ≤ 1.0 (the sweep's θ_m = 1.5 band is stall, not terrain — correction #10).\n"
        "At θ_m = 1.0: axle 4× at fixed R₀ moves the peak by 5%; R₀ 4× at fixed axle moves it by 560%.\n"
        "SUPERSEDED IN PART: §15/§17 show the peak is not proportional to R₀ within one controller family, and §18\n"
        "identifies the length as the body diameter.  Use this figure for R₀ versus axle only.\n"
        "Colour saturates at 3.0; R0-x2-axle-same reaches 10.46 at its peak.  " + NOT_BUILDABLE,
        annotate=["n", "duration", "start_radius"],
    )
    save_tight(fig, "figures/terrain_h2_powered.png")


def r0_scaling():
    r = load_jsonl("results/terrain_h2_r0_scaling.jsonl")
    fig = plot.surface(
        r,
        x="terrain.correlation_length",
        y="terrain.friction_amplitude",
        metric="final_dispersion",
        baseline_y=0.0,
        thresholds=[1.1, 1.25, 1.5],
        title="§4, H2 first pass: terrain does nothing once λ > R₀ — but this sweep cannot say WHICH length scale.\n"
        "Four rows differing only in the state-0 constant, so R₀ and λ/axle move together and are confounded;\n"
        "θ_m stops at 0.4, where the largest degradation is 40% and every cell still reaches a single cluster,\n"
        "so there is no transition on the grid to locate.  Each column divided by its own θ_m = 0 cell.\n"
        "SUPERSEDED by terrain_h2_powered.png, which breaks the confound and carries the θ_m range to find a peak.\n"
        "n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell.",
        annotate=["n", "duration", "start_radius"],
    )
    save_tight(fig, "figures/terrain_h2_r0_scaling.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["powered", "r0_scaling"]:
        globals()[name]()
