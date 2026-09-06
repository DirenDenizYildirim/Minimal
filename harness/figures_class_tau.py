"""Next-list item 8: does removing the truncation produce a transferring
rough-trained row?

§19 found its rough-trained class row keeping R₀ at 4.47 cm while the flat-trained
one moved to 7.47 cm and became the baseline, and attributed that to a truncated
training objective — at τ = 600 s almost no candidate aggregates at 3.0 m under
terrain, so those conditions had no gradient in them. S2-class-rough-tau is the
same search with τ = 3600 s at exactly those conditions, same budget, same
optimiser seed and the same training seed base, so trial length is the only
difference.

Three panels, left to right: what the search was minimising, what it actually
returned, and why.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE, _label
from swarm_harness.stats import wilson_ci

SUPTITLE = (
    "Next-list item 8: removing the truncation did not produce a transferring rough-trained row — and §19's diagnosis was wrong.\n"
    "Same class, same budget (1200 × 12), same optimiser seed, same training seed base (920 000); only τ at the 3.0 m conditions differs.\n"
    "R₀ moved 4.47 → 4.44 cm, i.e. not at all, and the row transfers no better: 6 W / 5 L / 1 tied on §14's grid against §19's 7 / 5 / 0.\n"
    "The cause is not the objective preferring a small R₀ — S2-class-flat scores 1.646 on this very objective against the returned row's 2.655.\n"
    "It is that the objective is estimated at 2 runs per condition, and one condition's noise is roughly six times the signal (panel C)."
)
ROWS = ["S2-gauci", "S2-class-flat", "S2-class-rough", "S2-class-rough-tau"]
COLOURS = {"S2-gauci": "#ff7f0e", "S2-class-flat": "#9467bd",
           "S2-class-rough": "#d62728", "S2-class-rough-tau": "#1f77b4"}
R0 = {"S2-gauci": 14.45, "S2-class-flat": 7.47,
      "S2-class-rough": 4.47, "S2-class-rough-tau": 4.44}

near = load_jsonl("results/terrain_class_objective_probe.jsonl")
far = load_jsonl("results/terrain_class_objective_probe_far.jsonl")
tau = load_jsonl("results/terrain_class_tau_eval_tau.jsonl")
CONDS = [(near, 0.74, 20, 600), (near, 0.74, 50, 600), (near, 1.5, 20, 600),
         (near, 1.5, 50, 600), (far, 3.0, 20, 3600), (far, 3.0, 50, 3600)]
LABELS = [f"{r:g} m\nn={n}\nτ={t}" for _, r, n, t in CONDS]

fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.6))

# --- A: the objective the rough class search was minimising ------------------
xs = np.arange(len(CONDS))
geo = {}
for row in ROWS:
    meds = []
    for src, rad, n, _ in CONDS:
        sub = src.filter(row=row, **{"swarm.init.radius": rad, "swarm.n": n})
        meds.append(float(np.median(np.asarray(sub.column("final_dispersion"), dtype=float))))
    g = float(np.exp(np.mean(np.log(meds))))
    geo[row] = g
    axes[0].plot(xs, meds, marker="o", ms=6, color=COLOURS[row],
                 label=f"{_label(row, near.filter(row=row))}  R₀ {R0[row]:.2f} cm   "
                       f"objective {g:.3f}")
    axes[0].axhline(g, color=COLOURS[row], ls=":", lw=1.0, alpha=0.7)
axes[0].set_xticks(xs)
axes[0].set_xticklabels(LABELS, fontsize=7.5)
axes[0].set_yscale("log")
axes[0].set_ylabel("median final dispersion per condition (log)\n"
                   "dotted: the geometric mean, which IS the objective", fontsize=9)
axes[0].set_title("A. The rough class objective, re-scored at 100 runs/condition\n"
                  "on its own training seeds", fontsize=9.5)
axes[0].legend(fontsize=7.5, frameon=False, loc="upper left")
axes[0].grid(alpha=0.25, lw=0.6)

# --- B: what the search returned, on held-out seeds ---------------------------
TAUS = tau.unique("sim.duration")
for row in ROWS:
    m, lo, hi = zip(*[wilson_ci(tau.filter(row=row, **{"sim.duration": t, "swarm.n": 20})
                                .column("ever_single_cluster")) for t in TAUS])
    axes[1].plot(TAUS, m, marker="o", ms=6, color=COLOURS[row],
                 label=_label(row, tau.filter(row=row)))
    axes[1].fill_between(TAUS, lo, hi, alpha=0.15, color=COLOURS[row], lw=0)
axes[1].axvline(600, color="0.55", ls="--", lw=1.0)
axes[1].annotate("τ §19 trained at", xy=(600, 0.02), xycoords=("data", "axes fraction"),
                 xytext=(4, 0), textcoords="offset points", fontsize=7.5, color="0.4")
axes[1].axvline(3600, color="#8a3b00", ls="--", lw=1.0)
axes[1].annotate("τ this row trained at", xy=(3600, 0.02), xycoords=("data", "axes fraction"),
                 xytext=(-6, 0), textcoords="offset points", fontsize=7.5, color="#8a3b00",
                 ha="right")
axes[1].set_xlabel("τ  (s)")
axes[1].set_ylim(0.0, 1.04)
axes[1].set_ylabel("reach at start radius 3.0 m, n = 20, θ_m = 0.9\n(Wilson 95%, held-out seeds)",
                   fontsize=9)
axes[1].set_title("B. Training at the longer τ did not help at the\n"
                  "condition it was meant to help", fontsize=9.5)
axes[1].legend(fontsize=8, frameon=False, loc="upper left")
axes[1].grid(alpha=0.25, lw=0.6)

# --- C: why — one condition's noise swamps the whole objective ---------------
v = np.asarray(far.filter(row="S2-class-rough-tau",
                          **{"swarm.init.radius": 3.0, "swarm.n": 20})
               .column("final_dispersion"), dtype=float)
rng = np.random.default_rng(7)
draws = np.array([np.median(rng.choice(v, 2, replace=False)) for _ in range(20000)])
axes[2].hist(draws, bins=np.geomspace(draws.min(), draws.max(), 40),
             color="#1f77b4", alpha=0.55, label="the 2-run estimate the search saw\n"
                                                "of this one condition, per evaluation")
lo, hi = np.percentile(draws, [5, 95])
axes[2].axvspan(lo, hi, color="#1f77b4", alpha=0.12, lw=0)
axes[2].annotate(f"5th–95th: {lo:.1f} → {hi:.1f}\n= {np.log(hi / lo):.2f} log units",
                 xy=(0.5, 0.72), xycoords="axes fraction", ha="center", fontsize=8.5,
                 color="#1f4f7f")
sig = np.log(geo["S2-class-rough-tau"] / geo["S2-class-flat"])
axes[2].annotate(f"the whole signal the search had to follow —\n"
                 f"the gap between the row it returned and the\n"
                 f"better one that already existed — is {sig:.2f} log units",
                 xy=(0.5, 0.40), xycoords="axes fraction", ha="center", fontsize=8.5,
                 color="#8a3b00")
axes[2].set_xscale("log")
axes[2].set_xlabel("median of 2 runs at 3.0 m, n = 20, τ = 3600 s")
axes[2].set_ylabel("evaluations (of 20 000 resamples)", fontsize=9)
axes[2].set_title("C. Why: at 2 runs per condition the noise in one cell\n"
                  "is ~6× the signal across the whole objective", fontsize=9.5)
axes[2].legend(fontsize=8, frameon=False, loc="upper left")
axes[2].grid(alpha=0.25, lw=0.6)

print(f"geometric means: " + ", ".join(f"{r} {geo[r]:.4f}" for r in ROWS))
print(f"signal between the returned row and S2-class-flat: {sig:.3f} log units")
print(f"2-run noise at the 3.0 m n=20 condition: {np.log(hi / lo):.3f} log units "
      f"({lo:.2f} to {hi:.2f})")

fig.suptitle(SUPTITLE, fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.80, bottom=0.155, left=0.065, right=0.99, wspace=0.30)
fig.text(0.5, 0.02, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_class_tau.png", dpi=160)
print("wrote figures/terrain_class_tau.png")
