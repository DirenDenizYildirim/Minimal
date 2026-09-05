import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from swarm_harness.load import load_jsonl
from swarm_harness.plot import UPPER_BOUND_NOTE

r = load_jsonl('results/terrain_mechanism_regression.jsonl')
META = {
    'axle-half-R0-same': (0.0255, 0.1445, '‡'),
    'base':              (0.051,  0.1445, ''),
    'axle-x2-R0-same':   (0.102,  0.1445, '‡'),
    'R0-half-axle-same': (0.051,  0.07225, '‡'),
    'R0-x2-axle-same':   (0.051,  0.2890, '‡'),
}
LAMBDA = 0.10

def pooled(rows, key):
    acc = {k: 0.0 for k in ('sum_x', 'sum_y', 'sum_xx', 'sum_xy', 'sum_yy')}
    n = 0
    for x in rows:
        f = x[key]
        n += f['n']
        for k in acc:
            acc[k] += f[k]
    N = float(n)
    sxx = acc['sum_xx'] - acc['sum_x'] ** 2 / N
    syy = acc['sum_yy'] - acc['sum_y'] ** 2 / N
    sxy = acc['sum_xy'] - acc['sum_x'] * acc['sum_y'] / N
    return sxy / sxx, sxy * sxy / (sxx * syy), n

pts = []
for name, (axle, R0, mark) in META.items():
    sub = r.filter(row=name).rows
    sf, rf, n = pooled(sub, 'steering_fit_full')
    sg, rg, _ = pooled(sub, 'steering_fit')
    pts.append((axle / LAMBDA, sf, rf, sg, rg, name + (f" {mark}" if mark else ""), R0))

pts.sort()
# Stagger labels: three rows share l/lambda = 0.51 and would otherwise overprint.
OFFSETS = {}
for x, *_rest in pts:
    OFFSETS.setdefault(round(x, 3), []).append(None)
seen = {}

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
for ax, (yi, label, ref) in zip(axes, [(1, "OLS slope", 1.0), (2, "R²", 1.0)]):
    seen.clear()
    for x, sf, rf, sg, rg, name, R0 in pts:
        full = (sf, rf)[yi - 1]
        grad = (sg, rg)[yi - 1]
        ax.scatter([x], [full], s=70, zorder=3, color="#1f77b4", marker="o")
        ax.scatter([x], [grad], s=70, zorder=3, color="#d62728", marker="s")
        k = round(x, 3)
        i = seen.get(k, 0)
        seen[k] = i + 1
        ax.annotate(f"{name}  (R₀ {R0*100:.1f} cm)", (x, full),
                    textcoords="offset points", xytext=(8, 8 - 13 * i),
                    fontsize=7, color="0.25")
    ax.axhline(ref, color="0.4", ls="--", lw=0.9)
    ax.axvline(1.0, color="0.75", ls=":", lw=1.0)
    ax.annotate("axle = λ", xy=(1.0, ax.get_ylim()[0]), xytext=(3, 6),
                textcoords="offset points", fontsize=7.5, color="0.5")
    # Room on the right for the axle-x2 labels, which otherwise run off.
    ax.set_xlim(0.15, 1.55)
    ax.set_xlabel("axle length / correlation length  (ℓ / λ)")
    ax.set_ylabel(label)
    ax.grid(alpha=0.25, lw=0.6)
axes[0].scatter([], [], color="#1f77b4", marker="o", label="full first-order expansion")
axes[0].scatter([], [], color="#d62728", marker="s", label="gradient term alone")
axes[0].legend(fontsize=8, frameon=False, loc="lower left")

fig.suptitle(
    "Experiment 3: the heading-rate residual IS the first-order per-wheel traction effect\n"
    "θ_m = 0.9, λ = 0.10 m, 12 million robot-timesteps pooled per row.  Slope → 1 and R² → 1 as ℓ/λ → 0,\n"
    "and both fall as ℓ/λ → 1, where a first-order expansion about the robot centre stops describing the wheels.\n"
    "The three points at ℓ/λ = 0.51 span a 4× range of R₀ and agree to 0.007 in slope: ℓ/λ decides this, R₀ does not.",
    fontsize=9, y=0.995, va="top")
fig.subplots_adjust(top=0.83, bottom=0.16, wspace=0.26)
fig.text(0.5, 0.015, UPPER_BOUND_NOTE, ha="center", fontsize=7.5, style="italic", color="#8a3b00")
fig.savefig("figures/terrain_mechanism_regression.png", dpi=160)
print("ok")
