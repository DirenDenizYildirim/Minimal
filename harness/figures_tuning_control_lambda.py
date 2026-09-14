"""Experiment 3 (freeze lift 1): the 2x2 tuning control at three correlation lengths.

Pre-registered at docs/preregistration/lambda-tuning-control.md (d6c40c8).

`figures_tuning_control.py` draws the lambda = 0.10 m experiment and is left
alone. This figure asks the reviewer's question instead: the decomposition was
measured at one correlation length, so does it depend on that choice? The three
lambdas are drawn side by side and NEVER pooled, because the pre-registered rule
is evaluated per lambda and a pooled panel would hide a lambda where it went the
other way.

Panel A is the quantity the rule turns on: the paired per-run difference
D(S2-flat) - D(S2-rough) against theta_m, one line per lambda, with zero drawn.
Above zero the terrain-trained row is the better one. The rule reads the
theta_m = 0.9 end; the theta_m = 0.6 crossing cell is marked because the
pre-registration asks for it to be reported at every lambda whether or not it
reappears.

Panel B is the matched-controller cost -- hold ratio minus one at theta_m = 0.9,
per row per lambda. A2 currently quotes 10-20% off lambda = 0.10 m alone and the
rule replaces that with the range over three, so the range is what the panel is
drawn to show.

Panel C is the level decomposition, which is deliberately NOT a paired ratio:
shares have to add to the whole gap, and only levels are additive. It is
reported, not thresholded.

THE LIMITATION THE FIGURE CANNOT DRAW ITS WAY OUT OF, stamped on it in the
caption. Both tuned rows were TRAINED at lambda = 0.10 m. At 0.05 and 0.20 m
this measures the transfer of a lambda = 0.10-tuned controller, not the
decomposition a lambda-matched controller would show, and a terrain term that
shrinks at a new lambda is consistent both with "the term is small everywhere"
and with "the term is real but does not transfer". Answering that would need a
search at each lambda, which is a different and much more expensive experiment.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import median_ci

ROWS = ["S2-gauci", "S2-flat", "S2-rough"]
TUNED = ["S2-flat", "S2-rough"]
ROUGH, FLAT = 0.9, 0.0
CROSSING = 0.6

# lambda = 0.10 m is the EXISTING record and is not re-run; it lives in the old
# file, where lambda is a row override and so carries no sweep coordinate.
OLD = load_jsonl("results/terrain_tuning_control.jsonl")
NEW = load_jsonl("results/terrain_tuning_control_lambda.jsonl")
SRC = {0.05: (NEW, {"terrain.correlation_length": 0.05}),
       0.10: (OLD, {}),
       0.20: (NEW, {"terrain.correlation_length": 0.20})}
LAMS = sorted(SRC)
AMS = OLD.unique("terrain.friction_amplitude")
LCOL = {0.05: "#1f77b4", 0.10: "#7f2f8f", 0.20: "#d62728"}
RCOL = {"S2-gauci": "#ff7f0e", "S2-flat": "#1f77b4", "S2-rough": "#2ca02c"}


def cells(lam, row, theta):
    rec, sel = SRC[lam]
    got = rec.filter(row=row, **{"terrain.friction_amplitude": theta}, **sel)
    return {x["run_index"]: x["final_dispersion"] for x in got.rows}


def paired(a, b):
    keys = sorted(set(a) & set(b))
    return median_ci([a[k] - b[k] for k in keys])


def hold(lam, row):
    r, f = cells(lam, row, ROUGH), cells(lam, row, FLAT)
    keys = sorted(set(r) & set(f))
    return median_ci([r[k] / f[k] for k in keys if f[k]])


fig, axes = plt.subplots(3, 1, figsize=(9.2, 11.0),
                         gridspec_kw={"height_ratios": [1.35, 1.0, 1.0]})

# ---- Panel A: the paired terrain term, per lambda, over the theta_m grid ----
ax = axes[0]
ax.axhline(0.0, color="0.4", ls="--", lw=1.0)
term = {}
for lam in LAMS:
    mid, los, his = [], [], []
    for a in AMS:
        m, lo, hi = paired(cells(lam, "S2-flat", a), cells(lam, "S2-rough", a))
        mid.append(m); los.append(lo); his.append(hi)
    term[lam] = (mid, los, his)
    ax.plot(AMS, mid, marker="o", ms=4.5, color=LCOL[lam],
            label=f"λ = {lam:.2f} m" + ("  (existing record)" if lam == 0.10 else ""))
    ax.fill_between(AMS, los, his, alpha=0.16, color=LCOL[lam], lw=0)
ax.axvline(ROUGH, color="0.75", lw=6, alpha=0.35, zorder=0)
ax.axvline(CROSSING, color="0.75", lw=6, alpha=0.20, zorder=0)
# Headroom is set BEFORE the annotations so neither of them lands on the frame:
# the top band label and the legend both live in the space this makes.
_lo, _hi = ax.get_ylim()
ax.set_ylim(_lo - 0.04 * (_hi - _lo), _hi + 0.26 * (_hi - _lo))
ax.annotate("the rule is\nevaluated here", xy=(ROUGH, 1.0), xycoords=("data", "axes fraction"),
            xytext=(-5, -5), textcoords="offset points", ha="right", va="top",
            fontsize=7.5, color="0.35")
ax.annotate("crossing cell", xy=(CROSSING, 0.0), xycoords=("data", "axes fraction"),
            xytext=(5, 5), textcoords="offset points", ha="left", va="bottom",
            fontsize=7.5, color="0.35")
ax.annotate("S2-flat better", xy=(0.015, 0.05), xycoords="axes fraction", fontsize=8, color="0.35")
ax.annotate("S2-rough better — terrain-tuning buys something",
            xy=(0.015, 0.95), xycoords="axes fraction", va="top", fontsize=8, color="0.35")
ax.set_ylabel("paired terrain term\nD(S2-flat) − D(S2-rough)\n(matched run index, 95%)", fontsize=9)
ax.set_xlabel("terrain.friction_amplitude  (θ_m)", fontsize=9)
ax.grid(alpha=0.25, lw=0.6)
ax.legend(fontsize=8.5, frameon=False, loc="upper left", bbox_to_anchor=(0.015, 0.90))

# ---- Panel B: the matched-controller cost, per row per lambda ----------------
ax = axes[1]
w = 0.26
xs = np.arange(len(LAMS))
holds = {row: [hold(lam, row) for lam in LAMS] for row in ROWS}
for i, row in enumerate(ROWS):
    vals = [100 * (h[0] - 1) for h in holds[row]]
    err = np.array([[100 * (h[0] - h[1]) for h in holds[row]],
                    [100 * (h[2] - h[0]) for h in holds[row]]])
    sub = SRC[0.10][0].filter(row=row)
    ax.bar(xs + (i - 1) * w, vals, w, yerr=err, capsize=3, color=RCOL[row],
           alpha=0.85, label=_label(row, sub), error_kw=dict(lw=1.0, ecolor="0.3"))
    for x, v, e in zip(xs + (i - 1) * w, vals, err[1]):
        # above the whisker, not on it -- at lambda = 0.10 m the S2-gauci error bar
        # is 30 points tall and a label at the bar top lands inside it.
        ax.annotate(f"{v:+.0f}%", xy=(x, v + e), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=7.5, color="0.25")
tuned = [100 * (hold(lam, row)[0] - 1) for lam in LAMS for row in TUNED]
ax.axhspan(min(tuned), max(tuned), color="#2ca02c", alpha=0.07, zorder=0)
ax.set_xticks(xs)
ax.set_xticklabels([f"λ = {l:.2f} m" for l in LAMS])
ax.set_ylabel("matched-controller cost\n(hold ratio − 1) at θ_m = 0.9, %", fontsize=9)
ax.grid(alpha=0.25, lw=0.6, axis="y")
_top = ax.get_ylim()[1]
ax.set_ylim(min(0.0, ax.get_ylim()[0]), _top * 1.22)
ax.legend(fontsize=8.5, frameon=False, ncol=3, loc="upper right")

# ---- Panel C: the level decomposition ---------------------------------------
ax = axes[2]
dec = {}
for lam in LAMS:
    d = {r: cells(lam, r, ROUGH) for r in ROWS}
    keys = sorted(set(d["S2-gauci"]) & set(d["S2-flat"]) & set(d["S2-rough"]))
    lev = {r: float(np.median([d[r][k] for k in keys])) for r in ROWS}
    gap = lev["S2-gauci"] - lev["S2-rough"]
    dec[lam] = (100 * (lev["S2-gauci"] - lev["S2-flat"]) / gap,
                100 * (lev["S2-flat"] - lev["S2-rough"]) / gap, gap)
obj = [dec[l][0] for l in LAMS]
ter = [dec[l][1] for l in LAMS]
ax.barh(xs, obj, 0.5, color="#8c8c8c", alpha=0.85, label="objective-tuning share")
ax.barh(xs, ter, 0.5, left=obj, color="#2ca02c", alpha=0.85, label="terrain-tuning share")
for x, (o, t, g) in zip(xs, [dec[l] for l in LAMS]):
    ax.annotate(f"{o:.1f} %", xy=(o / 2, x), ha="center", va="center", fontsize=8, color="w")
    ax.annotate(f"{t:+.1f} %   (gap {g:.3f})", xy=(100.5, x), ha="left", va="center", fontsize=8,
                color="0.25")
ax.axvline(100.0, color="0.4", ls="--", lw=1.0)
ax.set_yticks(xs)
ax.set_yticklabels([f"λ = {l:.2f} m" for l in LAMS])
ax.set_xlabel("share of the S2-gauci → S2-rough gap at θ_m = 0.9, %"
              "   (LEVELS, not paired ratios — only levels are additive)", fontsize=8.5)
ax.set_xlim(0, 138)
ax.set_ylim(-0.6, len(LAMS) - 0.15)
ax.grid(alpha=0.25, lw=0.6, axis="x")
# Outside the axes: at "lower right" the legend sat on the lambda = 0.05 m row's
# own share label.
ax.legend(fontsize=8.5, frameon=False, ncol=2, loc="lower right",
          bbox_to_anchor=(1.0, 1.02))

# ---- caption, computed rather than transcribed ------------------------------
rule = {lam: paired(cells(lam, "S2-flat", ROUGH), cells(lam, "S2-rough", ROUGH)) for lam in LAMS}
holds_ok = [f"λ={l:.2f}" for l in LAMS if rule[l][1] <= 0 <= rule[l][2]]
fails = [f"λ={l:.2f}" for l in LAMS if not (rule[l][1] <= 0 <= rule[l][2])]
cross = {lam: paired(cells(lam, "S2-flat", CROSSING), cells(lam, "S2-rough", CROSSING))
         for lam in LAMS}
cross_dj = [f"{l:.2f}" for l in LAMS if cross[l][1] > 0 or cross[l][2] < 0]
lo_c, hi_c = min(tuned), max(tuned)

fig.suptitle(
    "Experiment 3: the tuning control at three correlation lengths.  n = 20, τ = 600 s, R = 0.74 m, "
    "100 runs/cell, held-out seeds, three λ never pooled.\n"
    "The two searched rows were TRAINED at λ = 0.10 m: at 0.05 and 0.20 m this measures TRANSFER of a "
    "λ = 0.10-tuned controller, not a λ-matched decomposition.\n"
    f"A3 (the terrain-tuning interval includes zero) holds at {', '.join(holds_ok) or 'no λ'}"
    + (" by " + ", ".join(f"{abs(rule[l][1]):.4f}" for l in LAMS if rule[l][1] <= 0 <= rule[l][2])
       if holds_ok else "")
    + (f", and fails ABOVE zero at {', '.join(fails)}" if fails else "")
    + f".  Matched-controller cost across the three λ: {lo_c:+.0f}% to {hi_c:+.0f}%.\n"
    f"The θ_m = {CROSSING:g} crossing is disjoint from zero at "
    f"{len(cross_dj)} of {len(LAMS)} λ ({', '.join(cross_dj) or 'none'}) — the pre-registration "
    f"claims it only if that is more than one.",
    fontsize=8.6, y=0.996, va="top")
fig.subplots_adjust(top=0.885, bottom=0.075, left=0.155, right=0.965, hspace=0.34)
fig.text(0.5, 0.008, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_tuning_control_lambda.png", dpi=160, bbox_inches="tight")
print("wrote figures/terrain_tuning_control_lambda.png")
