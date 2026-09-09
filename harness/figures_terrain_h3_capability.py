"""§7 (Idea A, H3): the first terrain-aware capability row.

Ported from a `swarm-figure paired_panels` invocation whose arguments were never
recorded (verification-report D9). §10 describes it as "S2-gauci, S2-searched †,
S4-terrain †", and that is what this script draws from
`results/terrain_h3_capability.jsonl`.

THE CONTROL IS THE POINT. Without S2-searched the data reads as "the terrain bit
cuts degradation from 2.21 to 1.22" — a large apparent win for extra sensing, and
wrong. Re-searching the *same four constants* gets to 1.10, and the S = 4 row's
interval is disjointly worse. The honest statement is not "S = 4 is worse than
S = 2" but **no S = 4 controller better than the searched S = 2 one was found at
equal budget**; 600 evaluations over 8 constants is a thinner search per
dimension than 600 over 4.

TWO PANEL-ROWS, NOT ONE. The searched rows also aggregate tighter on flat ground
(1.427 / 1.253 / 1.222), so part of what the search bought is a better controller
in general, not terrain robustness. The hold ratio normalises each row by its own
flat baseline precisely so that cannot be read the wrong way — and reach is
plotted underneath because dispersion alone cannot say whether a swarm still
gets to a cluster at all.

REACH USES A PROPORTION INTERVAL. Its median is 1 whenever the majority succeed,
so a median panel draws a flat line at 1 while the probability falls. The first
version of this figure did exactly that and was wrong.

WHICH HOLD RATIO THIS PANEL DRAWS. `plot.paired_panels` divides each line by the
*median* of its own baseline cell, so the top row is the **ratio of medians** —
§7's own definition, and what its table quotes. `paper-source.md` §12.1 D1 asks
the paper to settle on the **paired per-run ratio** instead, because its interval
is computed on the same quantity as its point estimate; at the peak cell that is
2.149 [1.853, 2.455] / 1.099 [1.044, 1.145] / 1.212 [1.158, 1.251], against the
2.21 / 1.10 / 1.22 plotted here. The two disagree by at most 2.7% and not at all
in ordering or in disjointness, so the figure is unaffected — but a reader must
not take a number off this axis and quote it beside a paired one as if they were
different cells. They are the same 100 runs.
"""

from swarm_harness import plot
from swarm_harness.load import load_jsonl

r = load_jsonl("results/terrain_h3_capability.jsonl")

plot.paired_panels(
    r,
    x="terrain.friction_amplitude",
    metrics=[
        # baseline_x = 0.0: each line is divided by its own flat-ground value, so
        # rows that differ on clean ground cannot masquerade as differing under
        # terrain.
        ("final_dispersion", "hold ratio\ndispersion / own flat ground\n(median, bootstrap 95%)", 0.0),
        ("ever_single_cluster", "reach\nshare of runs ever in one cluster\n(Wilson 95%)", None, "proportion"),
    ],
    col_field="terrain.correlation_length",
    title="§7, H3: re-searching the four constants removes almost all the degradation; ADDING THE TERRAIN BIT DOES NOT HELP.\n"
    "At λ = 0.10 m, θ_m = 0.9: S2-gauci 2.21 [1.90, 2.41], S2-searched † 1.10 [1.08, 1.15], S4-terrain † 1.22 [1.16, 1.26]\n"
    "— the two searched rows have DISJOINT intervals, with the extra sensor state on the worse side.\n"
    "The hold ratio drawn here is the RATIO OF MEDIANS, §7's own definition.  Under the paired per-run ratio the paper\n"
    "settles on (§12.1 D1) the same cell reads 2.149 / 1.099 / 1.212 — same ordering, same disjointness, ≤2.7% apart.\n"
    "Honest statement: no S = 4 controller better than the searched S = 2 one was FOUND at equal budget.  600 evaluations\n"
    "over 8 constants is a thinner search per dimension than 600 over 4, and both S = 4 rows stay upper bounds.\n"
    "Both searched rows: same optimiser, same budget (600 × 12 = 7 200 runs), same training seeds, evaluation seeds disjoint.",
    annotate=["n", "duration", "start_radius"],
    out="figures/terrain_h3_capability.png",
)
print("wrote figures/terrain_h3_capability.png")
