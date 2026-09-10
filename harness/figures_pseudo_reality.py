"""Experiment 4: do the headline orderings survive a neighbourhood of the model?

Pre-registered at docs/preregistration/pseudo-reality.md (367ee93, +D1-D7).
One panel per comparison, models on the x axis, the statistic with its interval on
the y axis, the reference model marked, and the zero-or-one line drawn — which is
what the registration asked the figure to be.

EVERY NUMBER COMES FROM scripts/experiment4_decision.py, imported rather than
recomputed. A figure that reimplements its own statistics is a figure that can
disagree with the rule that decided the experiment, and the reader has no way to
tell which one is the result.

HOW DISJOINTNESS IS DRAWN, and why it is not an error bar everywhere. The rule
turns on two different things depending on the comparison:

  * C1 and C2 are PAIRED median differences of hold ratios, so the statistic has
    a bootstrap interval of its own and it is drawn as an error bar.
  * C3, C4 and C5 compare two Wilson intervals on proportions. The rule asks
    whether THOSE TWO intervals are disjoint, not whether an interval on their
    difference clears zero — so the point is drawn FILLED when the two sides are
    disjoint and HOLLOW when they overlap, and no error bar is invented for a
    difference the rule never puts one on.

Model 00 is the unperturbed reference and is drawn in black with a heavier marker,
separated from the ten sampled models by a rule, because it is the design point
the claims were measured at rather than a member of the family.

WHAT THIS FIGURE CANNOT SAY. The family perturbs implementation choices —
actuation noise, sensor dropout, contact-solver effort, timestep — around the
design point, and not the physics being modelled. A robust panel means robust to
how carefully the simulator is integrated and how noisy its sensors are, NOT to
whether the model is right. This is not a reality-gap study; §12.3 records that
none exists.
"""

import importlib.util
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.plot import UPPER_BOUND_NOTE

REPO = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "e4", REPO / "scripts" / "experiment4_decision.py")
e4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e4)

MODELS, SAMPLED = e4.MODELS, e4.SAMPLED
COL = plt.rcParams["axes.prop_cycle"].by_key()["color"]

# The timestep of each model, read from the same generator that drew the family.
# It is marked on the x axis because it is a property of the family, not a claim:
# the flip table the rule prints happens to separate perfectly on it, and a
# reader who cannot see which models are which cannot check that for themselves.
_gspec = importlib.util.spec_from_file_location(
    "gen", REPO / "scripts" / "build_pseudo_reality_configs.py")
_gen = importlib.util.module_from_spec(_gspec)
_gspec.loader.exec_module(_gen)
DT = {0: 0.10}
DT.update({i + 1: m["sim.dt"] for i, m in enumerate(_gen.sample())})
FINE = "#7f2f8f"      # dt = 0.05


def draw(ax, series, baseline, ylabel, title, errorbars):
    """One panel. `series` is [(label, colour, {model: entry})]."""
    ax.axhline(baseline, color="0.4", ls="--", lw=1.0, zorder=1)
    ax.axvline(0.5, color="0.75", lw=1.0, zorder=0)
    off = np.linspace(-0.22, 0.22, len(series)) if len(series) > 1 else [0.0]
    for (label, colour, per_model), dx in zip(series, off):
        ref = per_model[0]
        for m in MODELS:
            v = per_model[m]
            is_ref = m == 0
            flip = v["sign"] != ref["sign"]
            kw = dict(color="black" if is_ref else colour, zorder=4 if is_ref else 3)
            if errorbars:
                ax.errorbar([m + dx], [v["value"]],
                            yerr=[[v["value"] - v["lo"]], [v["hi"] - v["value"]]],
                            fmt="D" if is_ref else "o", ms=8 if is_ref else 5.5,
                            capsize=2.5, elinewidth=1.0,
                            markerfacecolor=(("black" if is_ref else colour)
                                             if v["disjoint"] else "none"),
                            markeredgewidth=1.4, **kw)
            else:
                ax.plot([m + dx], [v["value"]], "D" if is_ref else "o",
                        ms=8 if is_ref else 5.5,
                        markerfacecolor=(("black" if is_ref else colour)
                                         if v["disjoint"] else "none"),
                        markeredgewidth=1.4, **kw)
            if flip:
                ax.plot([m + dx], [v["value"]], "x", ms=11, color="#d62728",
                        markeredgewidth=2.0, zorder=5)
        ax.plot([], [], "o", color=colour, label=label)
    ax.set_xticks(MODELS)
    ax.set_xticklabels([f"{m:02d}" for m in MODELS], fontsize=7.5)
    for m, lbl in zip(MODELS, ax.get_xticklabels()):
        if DT[m] == 0.05:
            lbl.set_color(FINE)
            lbl.set_fontweight("bold")
    ax.set_xlim(-0.6, 10.6)
    ax.set_ylabel(ylabel, fontsize=8.2)
    ax.set_title(title, fontsize=9.2)
    ax.grid(alpha=0.22, lw=0.6)
    ax.annotate("ref", xy=(0, 1.0), xycoords=("data", "axes fraction"),
                xytext=(0, -3), textcoords="offset points", ha="center", va="top",
                fontsize=7, color="0.35")


fig, axes = plt.subplots(4, 2, figsize=(14.6, 16.0))

# ---- the reach diagnostic, as its own row of panels --------------------------
# Reported, NOT thresholded, and not part of the rule: the pre-registration fixed
# no reach contingency for this experiment and inventing one after the numbers
# were read is what a pre-registration prevents. It is on the figure because C1's
# ROBUST verdict partly rests on the enumerated row FAILING TO AGGREGATE in the
# noisier models rather than aggregating and being taxed, and a reader cannot
# check that from the C1 panel alone.
AGG_ROWS = ["S2-gauci"] + e4.CLASS_FLAT + ["S2-searched", "S4-terrain"]

ax = axes[0][0]
for i, row in enumerate(AGG_ROWS):
    vals, los, his = [], [], []
    for m in MODELS:
        c = e4.rec("aggregation", m).filter(
            row=row, **{"terrain.friction_amplitude": e4.ROUGH})
        pr, lo, hi = e4.wilson_ci([1.0 if x else 0.0 for x in c.column("ever_single_cluster")])
        vals.append(pr); los.append(lo); his.append(hi)
    heavy = row == "S2-gauci"
    ax.plot(MODELS, vals, marker="D" if heavy else "o", ms=6.5 if heavy else 4,
            lw=2.0 if heavy else 1.0, color="black" if heavy else COL[i % len(COL)],
            label=row + ("  (enumerated)" if heavy else ""), zorder=4 if heavy else 3)
    if heavy:
        ax.fill_between(MODELS, los, his, alpha=0.15, color="black", lw=0)
ax.axvline(0.5, color="0.75", lw=1.0, zorder=0)
ax.set_xticks(MODELS)
ax.set_xticklabels([f"{m:02d}" for m in MODELS], fontsize=7.5)
for m, lbl in zip(MODELS, ax.get_xticklabels()):
    if DT[m] == 0.05:
        lbl.set_color(FINE); lbl.set_fontweight("bold")
ax.set_xlim(-0.6, 10.6)
ax.set_ylim(0.55, 1.03)
ax.set_ylabel("reach at θ_m = 0.9\nfraction of runs ever a single cluster", fontsize=8.2)
ax.set_title("Reach diagnostic — reported, NOT thresholded, not part of the rule", fontsize=9.2)
ax.grid(alpha=0.22, lw=0.6)
ax.legend(fontsize=7.2, frameon=False, loc="lower right", ncol=2)
ax.annotate("ref", xy=(0, 1.0), xycoords=("data", "axes fraction"), xytext=(0, -3),
            textcoords="offset points", ha="center", va="top", fontsize=7, color="0.35")

ax = axes[0][1]
groups = {"reference\n(dt = 0.10,\nunperturbed)": [0],
          "sampled,\ndt = 0.10": [m for m in SAMPLED if DT[m] == 0.10],
          "sampled,\ndt = 0.05": [m for m in SAMPLED if DT[m] == 0.05]}
for gx, (label, ms) in enumerate(groups.items()):
    # Spread within the group: the dt = 0.10 models land within 0.03 of each
    # other and stack into an unreadable column at a single x.
    xs = ([gx] if len(ms) == 1
          else [gx + o for o in np.linspace(-0.16, 0.16, len(ms))])
    for x, m in zip(xs, sorted(ms)):
        c = e4.rec("aggregation", m).filter(
            row="S2-gauci", **{"terrain.friction_amplitude": e4.ROUGH})
        pr, _lo, _hi = e4.wilson_ci([1.0 if x else 0.0 for x in c.column("ever_single_cluster")])
        colour = "black" if m == 0 else (FINE if DT[m] == 0.05 else COL[0])
        ax.plot([x], [pr], "D" if m == 0 else "o", ms=8 if m == 0 else 6, color=colour)
        ax.annotate(f"{m:02d}", (x, pr), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=7.5, color=colour)
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(list(groups), fontsize=7.8)
ax.set_xlim(-0.5, len(groups) - 0.3)
ax.set_ylim(0.55, 1.03)
ax.set_ylabel("S2-gauci reach at θ_m = 0.9", fontsize=8.2)
ax.set_title("The same numbers, grouped by timestep", fontsize=9.2)
ax.grid(alpha=0.22, lw=0.6, axis="y")
ax.annotate("NOT the noise dials: model 01 draws the HIGHEST dropout of all\n"
            "(fn_rate 0.091) and reaches 0.97; model 08 draws the HIGHEST wheel\n"
            "noise (0.042) and reaches 0.97. Every perturbed dt = 0.10 model beats\n"
            "the noise-free reference, which is ADR 0004's own argument.\n"
            "Descriptive only — ten models, no model fitted.",
            xy=(0.03, 0.03), xycoords="axes fraction", fontsize=7.2, color="0.3", va="bottom")

axes = axes[1:]

draw(axes[0][0],
     [("S2-gauci − best-of-three S2-class-flat", COL[0], {m: e4.comparison_1(m) for m in MODELS})],
     0.0, "paired hold-ratio difference\nat θ_m = 0.9 (95%)",
     "C1 — terrain tax.  above 0: the enumerated row is taxed more", True)

draw(axes[0][1],
     [("S4-terrain † − S2-searched †", COL[2], {m: e4.comparison_2(m) for m in MODELS})],
     0.0, "paired hold-ratio difference\nat θ_m = 0.9, n = 20 (95%)",
     "C2 — capability flatness.  above 0: the terrain bit is worse", True)

draw(axes[1][0],
     [(row, COL[i], {m: e4.comparison_3(m, row) for m in MODELS})
      for i, row in enumerate(("B0-blind", "B1-ternary", "D-dispersive"))],
     1.0, "κ-response ratio\nsurvival at κ = 5 over κ = 0",
     "C3 — confusion through aggregation.  above 1: confusion buys survival", False)

draw(axes[1][1],
     [(f"r_p = {rp:g} m", COL[i], {m: e4.comparison_4(m, rp) for m in MODELS})
      for i, rp in enumerate(e4.RP)],
     0.0, "mean per-robot survival\nB1-ternary ‡ − D-dispersive ‡",
     "C4 — matched pair, pooled over κ.  above 0: the aggregating row survives better", False)

for j, reference in enumerate(("B0-blind", "B1-ternary")):
    draw(axes[2][j],
         [(f"r_p = {rp:g} m", COL[i], {m: e4.comparison_5(m, rp, reference) for m in MODELS})
          for i, rp in enumerate(e4.RP)],
         0.0, f"mean per-robot survival\nbest-of-three S3 † − {reference}",
         f"C5 — searched S = 3 † against {reference}.  above 0: the searched row wins", False)

for ax in axes[2]:
    ax.set_xlabel("pseudo-reality model  (00 = unperturbed reference)", fontsize=8.5)
for ax in axes.ravel():
    ax.legend(fontsize=7.6, frameon=False, loc="best")
axes = fig.axes  # restore, so nothing below indexes the trimmed view

fig.suptitle(
    "Experiment 4: pseudo-reality robustness.  Eleven models — 00 unperturbed, 01–10 drawn from the "
    "pre-registered seed 20260910 — at 100 runs/cell, paired WITHIN a model and never across models.\n"
    "FILLED = the comparison's two intervals are disjoint in that model;  HOLLOW = they overlap;  "
    "red × = the ordering runs the OTHER WAY from the reference model.  The rule counts both, per "
    "ordering, over the ten sampled models.\n"
    "The family perturbs wheel noise, sensor dropout, contact-solver effort and timestep — how carefully "
    "the simulator is integrated and how noisy its sensors are. It does NOT perturb the kinematics, the "
    "traction model, the pursuer's lock-on law or the sensor geometry,\n"
    "so a robust panel says nothing about whether the model is right. This is not a reality-gap study: "
    "no hardware, no ARGoS, no second simulator (§12.3).\n"
    "Model numbers in PURPLE BOLD are the five drawn at dt = 0.05 s; the rest, and the reference, "
    "run at dt = 0.10 s. Marked because the family separates on it, not as a claim about why.",
    fontsize=8.6, y=0.996, va="top")
fig.subplots_adjust(top=0.915, bottom=0.045, left=0.075, right=0.985, hspace=0.32, wspace=0.20)
fig.text(0.5, 0.010, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/pseudo_reality.png", dpi=160, bbox_inches="tight")
print("wrote figures/pseudo_reality.png")
