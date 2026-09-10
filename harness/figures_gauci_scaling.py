"""Validation §1: the Gauci reproduction and its scaling in swarm size.

Ported from a `swarm-figure` invocation whose arguments were never recorded
(verification-report D9). §10 describes it as "Gauci's constants, n = 2…100,
100 runs/cell", and that is what this script draws from
`results/gauci_scaling.jsonl` — which, with this file, is now the provenance.

Two panels because the week-1 gate turned on the difference between them. The
literature scores aggregation as **reaching** a connected configuration, not as
being in one at τ, and for a pair those are an order of magnitude apart: ~88% of
pairs reach contact, ~10% are still touching at τ. A figure showing only the
second would say this simulator disagrees with the source; it does not.

Reach is a proportion, so it gets a Wilson interval, not a bootstrap one: a
bootstrap of 100 successes out of 100 resamples 100 successes every time and
reports a zero-width interval at p = 1.

NOT A BYTE-FOR-BYTE PORT, and it cannot be one. The image this replaces was drawn
by a `swarm-figure` invocation whose arguments were never recorded, so there is
no committed original to compare against and no way to tell whether any
reconstruction is the same figure — the one attempt made during the verification
pass differed from the committed PNG in 44% of pixels. What this script
reproduces is the figure `paper-source.md` §10 *describes*. Written 2026-09-10,
in the freeze-lift-1 Phase 0 regeneration; nobody should read a later diff
against the lost image as a regression.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE
from swarm_harness.stats import median_ci, wilson_ci

# Gauci et al. (2014) report ~95.8% for this controller at n = 2; Steinberg &
# Solovey (2024) disprove the two-robot proof and measure 4.24% failures.
LITERATURE_REACH_N2 = 0.958

r = load_jsonl("results/gauci_scaling.jsonl")
NS = r.unique("n")

fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.9))

reach, rlo, rhi = [], [], []
disp, dlo, dhi = [], [], []
for n in NS:
    cell = r.filter(n=n)
    p, plo, phi = wilson_ci([1.0 if x else 0.0 for x in cell.column("ever_single_cluster")])
    reach.append(p)
    rlo.append(plo)
    rhi.append(phi)
    m, mlo, mhi = median_ci(cell.column("final_dispersion"))
    disp.append(m)
    dlo.append(mlo)
    dhi.append(mhi)
    print(f"n={n:3d}  reach {p:.2f} [{plo:.2f}, {phi:.2f}]  "
          f"dispersion {m:.3f} [{mlo:.3f}, {mhi:.3f}]")

axes[0].plot(NS, reach, marker="o", ms=5, color="#1f77b4")
axes[0].fill_between(NS, rlo, rhi, alpha=0.18, color="#1f77b4", lw=0)
axes[0].axhline(LITERATURE_REACH_N2, color="#8a3b00", ls="--", lw=1.1)
axes[0].annotate(
    f"Gauci et al. (2014) report ≈{LITERATURE_REACH_N2:.3g} at n = 2",
    xy=(0.5, LITERATURE_REACH_N2), xycoords=("axes fraction", "data"),
    xytext=(0, -12), textcoords="offset points", fontsize=8, color="#8a3b00",
)
axes[0].set_ylabel("reach: share of runs EVER in a single cluster\n(Wilson 95%)", fontsize=9)
axes[0].set_ylim(0.0, 1.05)

axes[1].plot(NS, disp, marker="o", ms=5, color="#2ca02c")
axes[1].fill_between(NS, dlo, dhi, alpha=0.18, color="#2ca02c", lw=0)
# The packing bound: a perfectly packed disc of n bodies scores ≈1 on the
# normalised second moment, so 1.15 at n = 100 is close to the floor, not
# "worse than the small swarms".
axes[1].axhline(1.0, color="0.5", ls=":", lw=1.0)
axes[1].annotate("≈1 = perfectly packed cluster", xy=(0.02, 1.0),
                 xycoords=("axes fraction", "data"), xytext=(0, 4),
                 textcoords="offset points", fontsize=8, color="0.35")
axes[1].set_yscale("log")
axes[1].set_ylabel("final dispersion, centroid frame\n(median, bootstrap 95%; log scale)", fontsize=9)

for ax in axes:
    ax.set_xscale("log")
    ax.set_xticks(NS)
    ax.set_xticklabels([str(n) for n in NS])
    ax.set_xlabel("swarm size n")
    ax.grid(alpha=0.25, lw=0.6)

fig.suptitle(
    "Validation §1: the Gauci reproduction.  x* = (−0.7, −1, 1, −1), binary LOS sensor, no memory, no arithmetic;\n"
    "n = 2…100, 100 runs/cell, τ = 600 s, dt = 0.1 s, start radius from the 5% coverage rule, collisions on.\n"
    "REACHING a connected configuration and BEING one at τ are different measurements and differ most at n = 2:\n"
    "~88% of pairs reach contact here, ~10% are still touching at τ.  The literature scores the first.",
    fontsize=9, y=0.995, va="top",
)
fig.subplots_adjust(top=0.855, bottom=0.13, left=0.085, right=0.985, wspace=0.26)
if r.any_upper_bound():
    fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
else:
    fig.text(0.5, 0.015,
             "Gauci's four constants are the only TIGHT minimum in this repository: "
             "an exhaustive grid search at its own resolution.  No †, no ‡.",
             ha="center", fontsize=7.5, style="italic", color="0.35")
fig.savefig("figures/gauci_scaling.png", dpi=160)
print("wrote figures/gauci_scaling.png")
