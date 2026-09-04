# Findings so far

Experimental results, as distinct from `docs/validation.md`, which records
whether the simulator can be trusted.

**Caveat.** The week-1 gate has passed (`docs/validation.md`), so the baseline is
trustworthy. Everything below is at n = 20 and τ = 600 s. Absolute dispersion
values still depend on a normalisation constant not yet checked against the
paper's figures; comparisons between cells are unaffected.

All numbers here were regenerated after the inter-wheel distance was corrected
to 5.1 cm.

Regenerate any table with the config named in its heading; every result is
seeded.

---

## 1. Week-3 shakedown: occlusion

`configs/sweeps/occlusion_shakedown.toml` — n = 20, τ = 600 s, 100 runs/cell,
two capability rows on a (false-negative rate × spatial correlation) grid.

**Rows.** M0 is Gauci's four constants, `c = (2, 0, 0, 0)`, enumerated and
therefore tight. M1 adds one bit of hysteresis — "saw a robot last step" —
giving `c = (2, 1, 0, 0)` and eight free constants. At Gauci's grid resolution
that is 20⁸ ≈ 2.6 × 10¹⁰ points, so M1 is **not** enumerable; the table used is
one hand-written point in that space, and any minimum read off the M1 row is an
**upper bound**. Searching those eight constants is the actual week-3 work, and
this sweep is what says whether it is worth running.

### The memory bit helps, everywhere

Median final dispersion (lower is more aggregated; the clean baseline is 1.43):

| false-negative rate | M0 (tight) | M1 hysteresis (upper bound) |
|---|---|---|
| 0.0 | 1.43 | 1.28 |
| 0.2 | 1.44 | 1.34 |
| 0.4 | 1.57 | 1.41 |
| 0.6 | 1.70 | 1.53 |
| 0.8 | 2.23 | 1.95 |
| 0.9 | 3.32 | 2.72 |

One bit buys a consistent improvement, including in the *clean* arena, and the
gap widens with the dropout rate. That is the answer the shakedown was for: the
eight-constant search is worth running.

### Spatially correlated dropout is worse — but mostly for a boring reason

At the same *nominal* rate, correlated dropout looks dramatically worse than
i.i.d.: at a nominal 0.6, dispersion is 4.15 correlated against 1.70 i.i.d.

It is largely an artefact of the nominal rate not being the realised one. The
correlated field is sampled where the robots actually are, and once a cluster
settles into a bad patch its readings are drawn from that patch, not from the
spatial average. The realised rate at a nominal 0.6 is **0.89**.

Binned by *realised* rate, most of the effect disappears (M0 row):

| realised FN rate | i.i.d. | correlated |
|---|---|---|
| 0.00–0.05 | 1.43 | 1.43 |
| 0.25–0.35 | 1.52 | 1.50 |
| 0.45–0.55 | 1.60 | 1.65 |
| 0.60–0.70 | 1.80 | 1.99 |
| 0.72–0.80 | 2.20 | 2.12 |
| 0.85–0.95 | 3.32 | **4.68** |
| 0.95–1.00 | — | 25.42 |

Below a realised rate of ~0.8 the two are within each other's spread. A genuine
extra penalty for spatial structure appears only above that, where the swarm can
get trapped in a patch that is effectively blind.

**Consequence for the write-up:** correlated and i.i.d. dropout must be compared
at matched *realised* rate, never at matched nominal rate. `realised_fn_rate` is
on every run record for exactly this reason. This is also a warning for the
terrain and pursuer dials: any dial whose intensity varies in space will have a
realised value that depends on where the swarm ends up.

Figures: `figures/occlusion_shakedown_curve.png`,
`figures/occlusion_shakedown_surface.png`.

---

## 2. Idea A: terrain

`configs/sweeps/terrain_idea_a.toml` — 100 runs/cell, `g_eff` = 0.4, correlation
length λ = 0.15 m ≈ R₀.

Median final dispersion (flat clean arena = 1.43):

| slope | θ_m = 0 | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| 0° | 1.43 | 1.40 | 1.41 | 1.49 | 1.63 |
| 2.5° | 1.39 | 1.41 | 1.43 | 1.46 | 1.74 |
| 5° | 1.42 | 1.44 | 1.46 | 1.47 | 1.76 |
| 7.5° | 1.47 | 1.43 | 1.47 | 1.50 | 1.78 |
| 10° | 1.42 | 1.49 | 1.48 | 1.55 | 1.93 |
| 15° | 1.51 | 1.52 | 1.59 | 1.68 | **2656** |

### Terrain degrades cluster *quality*, not the ability to aggregate

The share of runs that ever reach a single cluster is **1.00 in every cell**
except the runaway corner, where it is 0.52. So at n = 20 the terrain dials do
not stop the swarm aggregating; they make the cluster it forms looser, and make
it harder to hold. That distinction only became visible once the aggregation
criterion was corrected (ADR 0005), and it means a threshold `T` set on
"did they aggregate" would see almost nothing here while one set on dispersion
sees a clean monotone signal. **Set `T` on dispersion for Idea A.**

### H1 is not supported by this sweep

### H1 is not supported by this sweep

H1 predicts that *small* α and θ_m help, as motion noise did in Daymude et al.
The trend here is monotone degradation on both dials. The only hints in H1's
direction are marginal: θ_m = 0.1 sits a hair below the θ_m = 0 column at 0° and
7.5°, and α = 2.5° sits below α = 0° at θ_m = 0 (1.39 against 1.43). All are well
inside run-to-run spread, and they do not survive from one re-run to the next.

This is consistent with the actuation-noise result
(`docs/decisions/0004-baseline-actuation-noise.md`), where adding noise also
failed to help and mildly hurt. Two independent perturbations, same answer. The
"noise helps" intuition comes from a discrete model with a deterministic deadlock
to break; this continuous model does not appear to have one.

Note also that Daymude et al.'s mechanism is narrower than the analogy assumes:
noise there "perturbs the precise balancing of forces to allow robots to push
past one another" — it breaks a *contact deadlock*, and is not an exploration
argument. This continuous model has no such deadlock to break, which is
consistent with both null results.

**Next:** `configs/sweeps/terrain_h1_fine.toml` tests H1 on its own terms — a
dense neighbourhood of zero (α ≤ 3°, θ_m ≤ 0.1) at 200 runs/cell, rather than
read off the corner of a grid built for something else. If it fails there too,
H1 should be revised in the build doc, not quietly dropped.

### The (15°, θ_m = 0.5) cell is outside the model's usable range

Dispersion 2656 corresponds to the swarm spread over roughly 12 m, and it is the
one cell where reaching a single cluster fails outright (0.52 of runs). At that
corner `g_eff·sin α` = 0.104 m/s against a maximum wheel speed of 0.128 m/s, and
traction reaches 1.5, so robots are effectively rolling away downhill at
different rates. It is a real consequence of the model, not a numerical failure,
but it is a runaway regime rather than a degraded-aggregation one, and it should
be reported as the boundary of the dial range, not averaged into a trend.

### The dials are not interchangeable

At matched degradation the two dials behave differently: slope alone at 15°
reaches 1.51 and traction alone at θ_m = 0.5 reaches 1.63 — comparable — but the
runaway corner belongs to traction, and it is traction that pushes the swarm past
the point of aggregating at all. Slope keeps the swarm together and drags it;
traction breaks it up. That
distinction is what the two-dial surface is for, and it is the reason the build
doc's corrected model needs both mechanisms rather than one.

Figures: `figures/terrain_idea_a_surface.png`, `figures/terrain_idea_a_curve.png`.

---

## 3. Idea A, H1: does a *small* amount of terrain help?

`configs/sweeps/terrain_h1_fine.toml` — n = 20, **200 runs/cell**, a dense
neighbourhood of zero: α ∈ {0, 0.5, 1, 1.5, 2, 3}°, θ_m ∈ {0, 0.02, 0.05, 0.1},
`g_eff` = 0.4, λ = R₀.

**Answer: no.** Median final dispersion with 95% bootstrap CIs:

| slope | θ_m = 0 | 0.02 | 0.05 | 0.1 |
|---|---|---|---|---|
| 0° | 1.406 [1.389, 1.429] | 1.388 [1.360, 1.406] | 1.385 [1.371, 1.414] | 1.414 [1.399, 1.436] |
| 0.5° | 1.392 [1.374, 1.414] | 1.387 [1.367, 1.402] | 1.386 [1.366, 1.406] | 1.410 [1.393, 1.436] |
| 1° | 1.410 [1.388, 1.430] | 1.430 [1.393, 1.456] | 1.411 [1.382, 1.437] | 1.411 [1.389, 1.433] |
| 1.5° | 1.406 [1.389, 1.425] | 1.397 [1.385, 1.418] | 1.399 [1.384, 1.416] | 1.404 [1.377, 1.428] |
| 2° | 1.413 [1.389, 1.434] | 1.397 [1.378, 1.422] | 1.404 [1.388, 1.436] | 1.397 [1.377, 1.413] |
| 3° | 1.405 [1.386, 1.429] | 1.395 [1.376, 1.412] | 1.416 [1.389, 1.434] | 1.395 [1.381, 1.421] |

**Zero of the 23 non-baseline cells** has a confidence interval disjoint from the
clean baseline's. The entire grid sits between 1.385 and 1.430; every interval
overlaps every other. This is not a weak effect, it is no effect.

That is now three independent tests of the same prediction — actuation noise, the
coarse terrain grid, and this — and all three are null. **H1 should be revised in
the build doc, not quietly dropped.**

The reason is probably that the analogy was over-extended. Daymude et al.'s
mechanism is specific: noise "perturbs the precise balancing of forces to allow
robots to push past one another" — it breaks a *contact deadlock* in a discrete
model. It was never an argument that perturbation aids exploration, and this
continuous model has no such deadlock for it to break.

## 4. Idea A, H2: does the terrain transition scale with R₀?

`configs/sweeps/terrain_h2_r0_scaling.toml` — λ swept 0.0375–0.60 m against R₀
varied 7.65–48.45 cm via the state-0 wheel constants, 100 runs/cell. Because
changing those constants also changes speed and turn rate, every row is scored
**against its own θ_m = 0 cell**; the numbers below are degradation ratios, where
1.00 means terrain did nothing.

At θ_m = 0.4:

| row | R₀ | λ = 0.0375 | 0.075 | 0.15 | 0.30 | 0.60 |
|---|---|---|---|---|---|---|
| R0-07.7cm | 7.65 cm | 1.049 | 1.047 | 1.021 | 1.005 | 0.990 |
| R0-14.5cm | 14.45 cm | 1.105 | 1.140 | 1.055 | 0.985 | 0.991 |
| R0-23.0cm | 22.95 cm | 1.400 | 1.393 | 1.357 | 0.956 | 0.914 |
| R0-48.5cm | 48.45 cm | 1.050 | 1.274 | 1.294 | 1.065 | 1.067 |

**Partially supported, and the sweep was under-powered to say more.**

What holds: re-indexed by λ/R₀, every cell with λ/R₀ ≳ 1.3 sits at 0.91–1.07 —
terrain does nothing once its correlation length exceeds the loop it is meant to
deform. Every elevated cell has λ/R₀ ≲ 1. So R₀ *is* the scale that decides
whether terrain bites, which is H2's substantive claim, and swarm size plays no
part in it.

What does not hold: the curves do not collapse onto λ/R₀ alone. Within
λ/R₀ ≲ 1 the degradation ranges from 1.02 to 1.40, and it is ordered by R₀ —
the 7.65 cm row is nearly immune while the 22.95 cm row is worst. A second length
scale is in play, and the obvious candidate is the **axle length** (5.1 cm),
which is what decides whether the two wheels sample meaningfully different
traction in the first place. λ/R₀ and λ/ℓ are being varied together here and
cannot be separated by this design.

The sweep also cannot locate a *transition*, because at θ_m ≤ 0.4 there is not
one: the largest degradation is 40% in dispersion, and every cell still reaches a
single cluster. H2 is a statement about where aggregation **fails**, and this grid
never gets there.

**Next, and this is the concrete design H2 needs:**

1. Push θ_m to 0.6–1.0, where the coarse grid showed aggregation actually
   breaking, so there is a transition to locate rather than a slope to measure.
2. Separate λ/R₀ from λ/ℓ by varying the axle length independently of the wheel
   constants. Both are config fields, so this costs nothing but runs.
3. Only then fit the transition and test whether it tracks R₀.

Until that is done, H2 should be stated as "the effect vanishes for λ > R₀",
which is supported, rather than "the transition scales with R₀", which is not yet
tested.
