"""Experiment 4: does the gradient-steering fit collapse on ℓ/λ across λ?

Section 11 measured slope and R² at three axle lengths and one correlation
length, and read the trend as a function of ℓ/λ. With λ fixed, "a function of
ℓ/λ" and "a function of ℓ" are the same claim. This crosses three axles with
three λ so that the same ℓ/λ is reached by different (ℓ, λ) pairs, and asks
whether the points at matched ℓ/λ agree.

Marker shape carries λ. If the fit depends on ℓ/λ alone, shapes at the same x
sit on top of each other.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE

SUPTITLE = (
    "Experiment 4: the gradient-steering fit collapses on ℓ/λ across λ, not just across the axle\n"
    "θ_m = 0.9, n = 20, τ = 600 s, 12 million robot-timesteps pooled per point.  Three axles × three λ, arranged so the\n"
    "same ℓ/λ is reached by different (ℓ, λ) pairs.  Max slope spread at matched ℓ/λ is 0.0201 over a 4× range of λ,\n"
    "against a 0.86 span in slope along the trend itself — §11's ℓ/λ reading was not an axle effect wearing a ratio for a name."
)

r = load_jsonl("results/terrain_lambda_collapse.jsonl")
AXLE = {"axle-half-R0-same": 0.0255, "base": 0.051, "axle-x2-R0-same": 0.102}
MARK = {"axle-half-R0-same": "‡", "base": "", "axle-x2-R0-same": "‡"}
LAMS = r.unique("terrain.correlation_length")
MARKERS = {lam: m for lam, m in zip(LAMS, ["o", "s", "^", "D", "v"])}
COLOURS = {lam: c for lam, c in zip(LAMS, ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"])}


def pooled(rows, key):
    """Sum the streamed OLS sufficient statistics, then solve once."""
    acc = {k: 0.0 for k in ("sum_x", "sum_y", "sum_xx", "sum_xy", "sum_yy")}
    n = 0
    for x in rows:
        f = x[key]
        n += f["n"]
        for k in acc:
            acc[k] += f[k]
    N = float(n)
    sxx = acc["sum_xx"] - acc["sum_x"] ** 2 / N
    syy = acc["sum_yy"] - acc["sum_y"] ** 2 / N
    sxy = acc["sum_xy"] - acc["sum_x"] * acc["sum_y"] / N
    return sxy / sxx, sxy * sxy / (sxx * syy), n


pts = []
for row, axle in AXLE.items():
    for lam in LAMS:
        sub = r.filter(row=row, **{"terrain.correlation_length": lam}).rows
        if not sub:
            continue
        sf, rf, n = pooled(sub, "steering_fit_full")
        sg, rg, _ = pooled(sub, "steering_fit")
        pts.append(dict(row=row, axle=axle, lam=lam, x=axle / lam,
                        slope=sf, r2=rf, gslope=sg, gr2=rg, n=n))

groups: dict[float, list] = {}
for p in pts:
    groups.setdefault(round(p["x"], 4), []).append(p)

print(f"{'l/lam':>7} {'axle cm':>8} {'lam cm':>7} {'slope':>8} {'R2':>8} {'grad slope':>11} {'grad R2':>8} {'steps':>12}")
for x in sorted(groups):
    for p in sorted(groups[x], key=lambda q: q["lam"]):
        print(f"{p['x']:7.3f} {p['axle']*100:8.2f} {p['lam']*100:7.1f} {p['slope']:8.4f} "
              f"{p['r2']:8.4f} {p['gslope']:11.4f} {p['gr2']:8.4f} {p['n']:12d}")

print("\nspread at matched l/lambda (>=2 points):")
worst, worst_all = 0.0, 0.0
for x in sorted(groups):
    g = groups[x]
    if len(g) < 2:
        continue
    s = [p["slope"] for p in g]
    r2 = [p["r2"] for p in g]
    spread, r2spread = max(s) - min(s), max(r2) - min(r2)
    worst_all = max(worst_all, spread)
    narrow = [p for p in g if p["row"] != "axle-x2-R0-same"]
    if len(narrow) >= 2:
        worst = max(worst, max(p["slope"] for p in narrow) - min(p["slope"] for p in narrow))
    print(f"  l/lam = {x:.3f}: {len(g)} points, slope spread {spread:.4f}, R2 spread {r2spread:.4f}, "
          f"lambdas {[round(p['lam']*100, 1) for p in g]}")
print(f"\nmax slope spread at matched l/lambda: {worst_all:.4f} (all rows), "
      f"{worst:.4f} (excluding the widest axle)")

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))
for ax, key, label in ((axes[0], "slope", "OLS slope, full first-order expansion"),
                       (axes[1], "r2", "R², full first-order expansion")):
    for p in pts:
        ax.scatter([p["x"]], [p[key]], s=80, zorder=3, marker=MARKERS[p["lam"]],
                   color=COLOURS[p["lam"]], edgecolor="0.2", linewidth=0.6)
    ax.axhline(1.0, color="0.4", ls="--", lw=0.9)
    ax.axvline(1.0, color="0.75", ls=":", lw=1.0)
    ax.annotate("axle = λ", xy=(1.0, 0.02), xycoords=("data", "axes fraction"),
                xytext=(3, 0), textcoords="offset points", fontsize=7.5, color="0.5")
    ax.set_xscale("log")
    ax.set_xlabel("axle length / correlation length  (ℓ / λ)")
    ax.set_ylabel(label, fontsize=9)
    ax.grid(alpha=0.25, lw=0.6)
    # Log minor ticks label themselves into a smear over this one-decade range.
    ax.xaxis.set_major_locator(FixedLocator([0.125, 0.25, 0.5, 1.0, 2.0]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(ScalarFormatter())
for lam in LAMS:
    axes[0].scatter([], [], marker=MARKERS[lam], color=COLOURS[lam], edgecolor="0.2",
                    linewidth=0.6, label=f"λ = {lam * 100:g} cm")
axes[0].legend(fontsize=8.5, frameon=False, loc="lower left", title="marker = λ",
               title_fontsize=8.5)

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.80, bottom=0.155, left=0.075, right=0.98, wspace=0.22)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_lambda_collapse.png", dpi=160)
print("wrote figures/terrain_lambda_collapse.png")
