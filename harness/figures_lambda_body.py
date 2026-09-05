"""Question A, experiment 2: does the peak correlation length track the body?

§17 rejected proportionality to R₀, and §15 noted that the shared peak — 7.46 cm
— sits within 1% of the 7.4 cm body diameter. Body diameter is the one length in
the model that neither section varied, so this varies it: 3.7, 7.4 and 14.8 cm,
with R₀, the axle, the sensor model and the start radius held.

The statistic is the hold ratio, and it has to be. Dispersion is normalised by
robot radius squared and the cluster link distance is three body radii, so
absolute dispersion is not comparable across body sizes; a ratio of two
dispersions at the *same* body size cancels both.

The test is a log-log regression of peak λ on body diameter, with the slope
bootstrapped over the shared run-index axis. Slope 1 means the peak is the body
diameter; slope 0 means the body has nothing to do with it.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import bootstrap_ci, wilson_ci

SUPTITLE = (
    "Question A, experiment 2: the worst λ IS the body diameter.  R₀ (14.45 cm), axle, sensor model and start radius (0.74 m)\n"
    "held; body diameter 3.7 → 14.8 cm.  θ_m = 0.9, n = 20, τ = 600 s, 100 runs/cell, λ = 2 → 38.6 cm.\n"
    "Peak λ / body diameter = 1.01 at 7.4 cm and 0.97 at 14.8 cm; log-log slope 0.948 [0.474, 1.897], excluding 0 and containing 1.\n"
    "The 3.7 cm row reaches a cluster in at most 72% of runs at any λ — its flat-ground dispersion is 3.06 against 1.43 — so it is excluded.\n"
    "Recorded as the length the peak tracks. Link distance (1.5 body diameters) and occlusion footprint scale with the body too; no mechanism is claimed."
)
r = load_jsonl("results/terrain_lambda_body.jsonl")
ROWS = ["body-half", "body-base", "body-x2"]
DIAMETER = {"body-half": 0.037, "body-base": 0.074, "body-x2": 0.148}
colours = {"body-half": "#1f77b4", "body-base": "#ff7f0e", "body-x2": "#2ca02c"}
LAMS = r.unique("terrain.correlation_length")
AMS = r.unique("terrain.friction_amplitude")
REACH_FLOOR = 0.8
BOOT = 2000

data = {}
for row in ROWS:
    keys, cols, reach = None, [], []
    for lam in LAMS:
        flat = {x["run_index"]: x["final_dispersion"]
                for x in r.filter(row=row, **{"terrain.correlation_length": lam,
                                              "terrain.friction_amplitude": min(AMS)}).rows}
        rough = r.filter(row=row, **{"terrain.correlation_length": lam,
                                     "terrain.friction_amplitude": max(AMS)})
        rd = {x["run_index"]: x["final_dispersion"] for x in rough.rows}
        ks = sorted(set(flat) & set(rd))
        keys = ks if keys is None else keys
        assert ks == keys, "run indices differ between cells; the pairing is broken"
        cols.append([rd[k] / flat[k] for k in ks])
        reach.append(wilson_ci(rough.column("ever_single_cluster")))
    data[row] = dict(matrix=np.asarray(cols).T, reach=reach, records=r.filter(row=row))


def peak(row, resample=None):
    d = data[row]
    m = d["matrix"] if resample is None else d["matrix"][resample]
    curve = np.median(m, axis=0)
    ok = [j for j, (p, _, _) in enumerate(d["reach"]) if p >= REACH_FLOOR]
    return LAMS[max(ok, key=lambda j: curve[j])] if ok else None


rng = np.random.default_rng(20260905)
n_runs = data[ROWS[0]]["matrix"].shape[0]
draws = [rng.integers(0, n_runs, n_runs) for _ in range(BOOT)]

peaks = {row: peak(row) for row in ROWS}
boot_peaks = {row: [peak(row, d) for d in draws] for row in ROWS}
usable = [row for row in ROWS if peaks[row] is not None]

for row in ROWS:
    d = data[row]
    inside = sum(1 for p, _, _ in d["reach"] if p >= REACH_FLOOR)
    if peaks[row] is None:
        print(f"{row:>10} body {DIAMETER[row]*100:5.1f} cm  NO VALID λ "
              f"(max reach {max(p for p, _, _ in d['reach']):.2f})")
    else:
        ps = [p for p in boot_peaks[row] if p is not None]
        lo, hi = np.percentile(ps, [2.5, 97.5])
        print(f"{row:>10} body {DIAMETER[row]*100:5.1f} cm  peak λ = {peaks[row]*100:6.2f} cm "
              f"[{lo*100:.2f}, {hi*100:.2f}]  peak/diameter = {peaks[row]/DIAMETER[row]:.2f}  "
              f"({inside}/{len(LAMS)} λ inside the window)")

# The sensitivity that decides how much weight the headline carries: the same
# regression on ALL three rows, using each row's unrestricted argmax. The
# excluded row's argmax is 7.46 cm against a 3.7 cm body — a ratio of 2, not 1 —
# so the slope depends on the validity window and the section has to say by how
# much rather than report only the number the window produces.
def unrestricted_peak(row):
    curve = np.median(data[row]["matrix"], axis=0)
    return LAMS[int(np.argmax(curve))]


all_x = np.log([DIAMETER[row] for row in ROWS])
all_y = np.log([unrestricted_peak(row) for row in ROWS])
all_slope = np.polyfit(all_x, all_y, 1)[0]
print("unrestricted argmax per row: "
      + ", ".join(f"{row} {unrestricted_peak(row)*100:.2f} cm "
                  f"(= {unrestricted_peak(row)/DIAMETER[row]:.2f} diameters)" for row in ROWS))
print(f"log-log slope on ALL THREE rows, ignoring the validity window: {all_slope:.3f}")

slope_ci = None
if len(usable) >= 2:
    xs = np.log([DIAMETER[row] for row in usable])
    slopes = []
    for b in range(BOOT):
        ys = [boot_peaks[row][b] for row in usable]
        if any(y is None for y in ys):
            continue
        slopes.append(np.polyfit(xs, np.log(ys), 1)[0])
    point = np.polyfit(xs, np.log([peaks[row] for row in usable]), 1)[0]
    slope_ci = (point, *np.percentile(slopes, [2.5, 97.5]))
    print(f"\nlog-log slope of peak λ on body diameter over {len(usable)} usable rows: "
          f"{point:.3f} [{slope_ci[1]:.3f}, {slope_ci[2]:.3f}]  "
          f"(1 = peak IS the body diameter, 0 = body irrelevant)")

fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.6))
for row in ROWS:
    d = data[row]
    mid = np.median(d["matrix"], axis=0)
    lo, hi = zip(*[bootstrap_ci(d["matrix"][:, j]) for j in range(len(LAMS))])
    inside = [p >= REACH_FLOOR for p, _, _ in d["reach"]]
    axes[0].plot(LAMS, mid, color=colours[row], lw=1.4,
                 label=f"{_label(row, d['records'])}  (body {DIAMETER[row]*100:.1f} cm)")
    axes[0].fill_between(LAMS, lo, hi, alpha=0.14, color=colours[row], lw=0)
    for x, y, ok in zip(LAMS, mid, inside):
        axes[0].plot([x], [y], marker="o", ms=5, color=colours[row],
                     mfc=colours[row] if ok else "white", mew=1.3)
    axes[0].axvline(DIAMETER[row], color=colours[row], ls="--", lw=1.0, alpha=0.7)

for row in usable:
    ps = [p for p in boot_peaks[row] if p is not None]
    lo, hi = np.percentile(ps, [2.5, 97.5])
    axes[1].errorbar([DIAMETER[row]], [peaks[row]],
                     yerr=[[peaks[row] - lo], [hi - peaks[row]]],
                     fmt="o", ms=9, capsize=4, color=colours[row], zorder=3,
                     label=f"body {DIAMETER[row]*100:.1f} cm")
lim = [0.03, 0.17]
axes[1].plot(lim, lim, color="0.45", ls="--", lw=1.1, label="peak λ = body diameter (slope 1)")
axes[1].axhline(0.0746, color="0.35", ls=":", lw=1.3)
axes[1].annotate("§15's 7.46 cm", xy=(0.02, 0.0746), xycoords=("axes fraction", "data"),
                 xytext=(0, 4), textcoords="offset points", fontsize=8, color="0.3")
axes[1].set_xlabel("body diameter  (m)")
axes[1].set_ylabel("peak λ  (m)", fontsize=9)
axes[1].set_xscale("log")
axes[1].set_yscale("log")
axes[1].legend(fontsize=8.5, frameon=False, loc="upper left")

axes[0].set_xscale("log")
axes[0].set_yscale("log")
axes[0].axhline(1.0, color="0.5", ls=":", lw=1.0)
axes[0].set_xlabel("terrain.correlation_length  λ  (m)\n"
                   "dashed verticals: each row's own body diameter", fontsize=9)
axes[0].set_ylabel("hold ratio (log)\nθ_m = 0.9 / own flat ground, paired, 95%", fontsize=9)
axes[0].plot([], [], marker="o", ms=5, ls="none", color="0.4", mfc="white", mew=1.3,
             label=f"hollow: reach < {REACH_FLOOR} at θ_m = 0.9, excluded from the peak")
axes[0].legend(fontsize=8.5, frameon=False, loc="upper left")
for ax, ticks in ((axes[0], [0.02, 0.05, 0.1, 0.2, 0.4]), (axes[1], [0.04, 0.07, 0.15])):
    ax.grid(alpha=0.25, lw=0.6)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(ScalarFormatter())
axes[1].yaxis.set_major_locator(FixedLocator([0.03, 0.05, 0.075, 0.1, 0.15]))
axes[1].yaxis.set_minor_locator(NullLocator())
axes[1].yaxis.set_major_formatter(ScalarFormatter())

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.80, bottom=0.175, left=0.085, right=0.985, wspace=0.22)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_lambda_body.png", dpi=160)
print("wrote figures/terrain_lambda_body.png")
