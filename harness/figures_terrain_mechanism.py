"""§6 (Idea A mechanism test): deformation, or speed heterogeneity?

Ported from a `swarm-figure` invocation whose arguments were never recorded
(verification-report D9). §10 describes it as "per-wheel vs scalar-centre, paired
seeds", and that is what this script draws from `results/terrain_mechanism.jsonl`.

THE CONTROL. A scalar speed field still makes robots in different places move at
different rates, which alone changes who meets whom. If that were the mechanism,
curvature would be incidental and the corrected per-wheel model would be
unnecessary. The two rows here use the **same placements and the same traction
field** and differ only in how the field is sampled: per-wheel (each wheel reads
its own traction, so the robot's path curves) versus scalar-centre (both wheels
read the body centre, so speed varies but heading does not).

THE PRE-REGISTERED RULE, and which branch fired: if the scalar row reproduced the
per-wheel row's peak location *and* magnitude within CI, the mechanism was
relative speed heterogeneity and the curvature explanation was to be retired. It
does not reproduce — the scalar row has no peak at all and sits flat in
[0.96, 1.01] across the whole grid — so the curvature explanation stands.

One panel per row, on a shared y axis, rather than a colour surface: the claim is
that one row HAS a peak at λ/R₀ ≈ 0.69 and the other has none, and an absence is
much easier to read as a flat line through 1.0 than as an evenly coloured patch.
The y axis has to be shared or the scalar row's ±2% band would be stretched to
fill its own panel and look like structure.

Both rows are Gauci's enumerated constants, so neither carries † nor ‡: what
varies is the environment model, not the controller.

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
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.stats import median_ci

R0_GAUCI = 0.1445  # m — the state-0 turn radius the λ/R₀ axis is read against.
ROWS = ["per-wheel", "scalar-centre"]
COLOURS = {"per-wheel": "#d62728", "scalar-centre": "#1f77b4"}

r = load_jsonl("results/terrain_mechanism.jsonl")
LAMS = r.unique("terrain.correlation_length")
AMPS = r.unique("terrain.friction_amplitude")
FLAT = min(AMPS)


def hold_ratio(row, lam, amp):
    """Dispersion at `amp` over the same run's dispersion on flat ground.

    Paired by run index: both cells were run from the same placements and the
    same field, so the ratio removes the run-to-run draw rather than averaging
    over it. This is the statistic §6's table reports.
    """
    flat = {x["run_index"]: x["final_dispersion"]
            for x in r.filter(row=row, **{"terrain.correlation_length": lam,
                                          "terrain.friction_amplitude": FLAT}).rows}
    rough = r.filter(row=row, **{"terrain.correlation_length": lam,
                                 "terrain.friction_amplitude": amp}).rows
    return [x["final_dispersion"] / flat[x["run_index"]]
            for x in rough if x["run_index"] in flat and flat[x["run_index"]]]


fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.6), sharey=True)
POOLED = {}

for ax, row in zip(axes, ROWS):
    for amp in [a for a in AMPS if a != FLAT]:
        med, lo, hi = [], [], []
        for lam in LAMS:
            m, l, h = median_ci(hold_ratio(row, lam, amp))
            med.append(m); lo.append(l); hi.append(h)
        shade = 0.75 - 0.55 * (amp / max(AMPS))
        colour = mcolors.to_rgb(COLOURS[row])
        colour = tuple(c * (1 - shade) + shade for c in colour)
        ax.plot([l / R0_GAUCI for l in LAMS], med, marker="o", ms=4.5,
                color=colour, label=f"θ_m = {amp:g}")
        ax.fill_between([l / R0_GAUCI for l in LAMS], lo, hi, alpha=0.16, color=colour, lw=0)
    pooled = [v for amp in AMPS if amp != FLAT for lam in LAMS for v in hold_ratio(row, lam, amp)]
    POOLED[row] = median_ci(pooled)
    ax.set_title(f"{row}   pooled over every θ_m > 0 cell: "
                 f"{POOLED[row][0]:.3f} [{POOLED[row][1]:.3f}, {POOLED[row][2]:.3f}]  (n = {len(pooled)})",
                 fontsize=9.5)
    ax.axhline(1.0, color="0.45", ls=":", lw=1.1)
    ax.axvline(0.69, color="#8a3b00", ls="--", lw=1.1)
    ax.annotate("λ/R₀ = 0.69", xy=(0.69, 0.02), xycoords=("data", "axes fraction"),
                xytext=(4, 0), textcoords="offset points", fontsize=8, color="#8a3b00")
    ax.set_xscale("log")
    ax.set_xlabel("λ / R₀   (R₀ = 14.45 cm, Gauci)")
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(fontsize=8.5, frameon=False, title="friction amplitude", title_fontsize=8.5)
    print(f"{row}: pooled {POOLED[row][0]:.4f} [{POOLED[row][1]:.4f}, {POOLED[row][2]:.4f}]")

axes[0].set_yscale("log")
axes[0].set_ylabel("hold ratio\ndispersion at θ_m / same run's flat ground\n(paired by run index, median, bootstrap 95%)",
                   fontsize=9)

fig.suptitle(
    "§6 mechanism test: the curvature explanation stands.  Both rows use Gauci's enumerated constants, the SAME\n"
    "placements and the SAME traction field, and differ only in how the field is sampled — per-wheel (each wheel\n"
    "reads its own traction, so the path curves) against scalar-centre (both wheels read the body centre, so speed\n"
    "varies but heading does not).  n = 20, τ = 600 s, start radius 0.74 m, 100 runs/cell, slope 0.\n"
    "Pre-registered rule: if the scalar row reproduced the per-wheel row's peak in location AND magnitude within CI,\n"
    "the mechanism was speed heterogeneity.  It has NO peak and is flat within [0.96, 1.01] across the whole grid.",
    fontsize=9, y=0.995, va="top",
)
fig.subplots_adjust(top=0.805, bottom=0.175, left=0.115, right=0.985, wspace=0.07)
fig.text(0.5, 0.05,
         "Reported without explanation, per the rule: the scalar row sits slightly BELOW 1.0 — pooled "
         f"{POOLED['scalar-centre'][0]:.3f} [{POOLED['scalar-centre'][1]:.3f}, {POOLED['scalar-centre'][2]:.3f}], an interval excluding 1.0.\n"
         "A pure scalar speed field appears to aggregate ~2% better than flat ground.  Not in H1's direction, "
         "at the edge of what this design resolves, and never chased.",
         ha="center", va="bottom", fontsize=7.5, style="italic", color="0.35")
# Both rows are Gauci's enumerated constants: what varies here is the environment
# model, not the controller, so neither provenance stamp belongs on this figure.
fig.text(0.5, 0.012,
         "Both rows use Gauci's enumerated controller — a TIGHT minimum, not an upper bound.  No †, no ‡.  "
         "What varies is the traction model, not the capability.",
         ha="center", va="bottom", fontsize=7.5, style="italic", color="0.45")
fig.savefig("figures/terrain_mechanism.png", dpi=160)
print("wrote figures/terrain_mechanism.png")
