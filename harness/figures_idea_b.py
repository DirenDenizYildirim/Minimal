"""Idea B figures (§5 and §8), regenerated with r_p reported in start radii.

r_p in metres says nothing on its own. The swarm starts inside a disc of radius
0.74 m, so r_p = 1.0 m is not the hard end of a difficulty axis — it is a pursuer
that sees the entire starting swarm from anywhere in it. `plot.label_pursuer_range`
puts both numbers on the axis and marks that corner; this script is where the
commands that produced the committed figures live, so they can be re-run.
"""

import sys

from swarm_harness import plot
from swarm_harness.load import load_jsonl

R_START = 0.74  # metres; every Idea B sweep starts the swarm inside this disc.


def corner_note(ranges) -> str:
    over = [r for r in ranges if r >= R_START]
    listed = ", ".join(f"{r:g} m" for r in over) if over else "none of them"
    return (f"r_p / start radius: " + ", ".join(f"{r:g}→{r / R_START:.2f}R" for r in ranges)
            + f".  Perfect-perception corner (r_p ≥ {R_START:g} m): {listed}.")


def first_pass():
    r = load_jsonl("results/pursuer_idea_b.jsonl")
    ranges = r.unique("pursuer.range")
    plot.surface(
        r,
        x="pursuer.range",
        y="pursuer.confusion",
        metric="survival_fraction",
        thresholds=[0.25, 0.5, 0.75],
        title="Idea B, first pass: survival fraction over (r_p, κ)\n"
        "Start radius 0.74 m, so r_p = 1.0 m is the perfect-perception corner, not the hard end of the axis\n"
        + corner_note(ranges),
        annotate=["pursuer_speed_ratio", "pursuer_handling_time", "n", "duration", "start_radius"],
        out="figures/pursuer_idea_b_surface.png",
    )
    print("wrote figures/pursuer_idea_b_surface.png")


def dispersive():
    r = load_jsonl("results/pursuer_dispersive_h1.93.jsonl")
    ranges = r.unique("pursuer.range")
    plot.surface(
        r,
        x="pursuer.range",
        y="pursuer.confusion",
        metric="survival_fraction",
        thresholds=[0.3, 0.5, 0.7],
        title="Idea B: does aggregation explain survival rising with confusion?  (5×5 grid, 100 runs/cell, h = 1.93 s)\n"
        "D-dispersive has B1's sensing and flee response but a 99 cm state-0 arc, so no cluster forms\n"
        "All three rows are hand-designed spatial strategies; they isolate strategy, not what S = 3 sensing can do\n"
        + corner_note(ranges),
        annotate=["pursuer_speed_ratio", "pursuer_handling_time", "n", "duration", "start_radius"],
        out="figures/pursuer_dispersive_surface.png",
    )
    print("wrote figures/pursuer_dispersive_surface.png")

    full = load_jsonl("results/pursuer_dispersive.jsonl")
    plot.paired_panels(
        full,
        x="pursuer.confusion",
        metrics=[("survival_fraction", "survival fraction\n(median, pooled over r_p)", None)],
        col_field="pursuer.handling_time",
        title="Idea B: confusion helps the aggregating rows and barely moves the dispersive one\n"
        "Pooled over r_p ∈ {0.1, 0.2, 0.35, 0.6, 1.0} m = {0.14, 0.27, 0.47, 0.81, 1.35} start radii;\n"
        "the r_p = 1.0 m column is the perfect-perception corner and is pooled in with the rest",
        annotate=["pursuer_speed_ratio", "n", "duration", "start_radius"],
        out="figures/pursuer_dispersive_kappa.png",
    )
    print("wrote figures/pursuer_dispersive_kappa.png")


if __name__ == "__main__":
    which = sys.argv[1:] or ["first_pass", "dispersive"]
    for name in which:
        globals()[name]()
