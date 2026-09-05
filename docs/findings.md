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

Two sweeps. The first (`terrain_h2_r0_scaling`) established that terrain does
nothing once λ > R₀, but at θ_m ≤ 0.4 there was no transition to locate — only a
40% slope — and it could not separate λ/R₀ from λ/axle, because varying the wheel
constants varies both together.

`configs/sweeps/terrain_h2_powered.toml` fixes both: θ_m runs to 1.5, and five
rows break the confound by holding one length scale fixed while varying the
other. Every row is scored against its own θ_m = 0 cell at the same λ.

### The answer: R₀ controls it, the axle does not

Peak degradation and where it occurs, at θ_m = 0.7:

| row | axle | R₀ | peak λ | **λ/R₀** | λ/axle | peak degradation |
|---|---|---|---|---|---|---|
| axle-half-R0-same | 2.55 cm | 14.45 cm | 0.100 | **0.69** | 3.92 | 1.40 |
| base | 5.10 cm | 14.45 cm | 0.100 | **0.69** | 1.96 | 1.58 |
| axle-x2-R0-same | 10.20 cm | 14.45 cm | 0.100 | **0.69** | 0.98 | 1.34 |
| R0-half-axle-same | 5.10 cm | 7.22 cm | 0.050 | **0.69** | 0.98 | 1.17 |
| R0-x2-axle-same | 5.10 cm | 28.90 cm | 0.100 | 0.35 | 1.96 | 2.69 |

The peak sits at **λ/R₀ ≈ 0.7** for four of the five rows, across a four-fold
range of axle length, while λ/axle over those same rows scatters from 0.98 to
3.92. The fifth row's peak falls between two grid points (λ/R₀ of 0.35 and 0.69
score 2.69 and 2.43), so the λ grid, not the physics, sets that entry.

The magnitudes settle it. At θ_m = 1.0:

* varying the **axle 4×** at fixed R₀ = 14.45 cm: peak degradation 2.83, 2.97,
  2.93 — a spread of **5%**;
* varying **R₀ 4×** at fixed axle = 5.10 cm: peak degradation 1.59, 2.97, 10.46
  — a spread of **560%**.

**H2 is supported.** The terrain transition is set by R₀, the controller's own
intrinsic length scale, and not by the robot's wheel geometry — and not, as the
build doc emphasises, by swarm size. The natural reading is that R₀ is the
distance over which deformation accumulates before the trajectory closes, so
terrain structure comparable to R₀ has maximum leverage; structure much finer
averages out along the loop, and structure much coarser looks like a uniform
offset the whole loop shares.

That the *axle* barely matters is the more surprising half, since the axle is
what makes the two wheels sample different traction in the first place. Evidently
that per-step asymmetry is not the limiting factor — what matters is how far the
robot travels while the terrain stays correlated.

### Where the model stops being about robots

The sweep originally ran to θ_m = 1.5, where every row degraded 6–14× and the
ordering by R₀ collapsed. That band is **not terrain**: the field reaches
|f| = 1, so above θ_m = 1 the traction multiplier can reach zero, a wheel stalls
and the robot pivots. It has been cut from the swept range rather than explained
— see §6 — and the figure now stops at θ_m = 1.0.

One row is not a robot at all: `axle-x2-R0-same` puts the wheel contacts outside
the 7.4 cm body. It exists to break the R₀/axle confound numerically, and no
result from it describes a buildable machine. It is what makes the 5% spread
above meaningful, so it stays in, labelled, and the caveat is in the figure
caption as well as here.

All five rows are hand-picked points rather than searched controllers, so they
carry ‡ in the figure. That mark is about how the constants were obtained; these
rows are not minimality claims at all.

Figure: `figures/terrain_h2_powered.png`.

### What this leaves for the anisotropy lemma

The build doc wants a theorem of the form "aggregation holds if the anisotropy
ratio is below f(R₀, sensor range)". The measurement now says what f should
depend on: R₀ and the terrain correlation length, in the ratio λ/R₀, with the
worst case near 0.7. That is a much narrower target than the sweep started with,
and it is the natural next piece of analysis.

---

## 5. Idea B, first pass: the pursuer with imperfect perception

`configs/sweeps/pursuer_idea_b.toml` — n = 20, **τ = 120 s**, ρ = 1.5, handling
time 5 s, start radius 0.74 m, four capability rows on a **5 × 5** grid of
`r_p` × `κ`, 100 runs/cell, 10 000 trials. 8.8% of runs ended in a wipeout.

**Rows B0–B3 only.** B4 needs a received alarm bit and communication is not
wired — `rx` is held at 0, so a K = 1 row would silently behave as K = 0.
B1–B3 are **hand-designed (‡), not searched**.

### Median survivors out of 20

| κ | r_p | B0 blind | B1 ternary ‡ | B2 ternary+side ‡ | B3 ternary+memory ‡ |
|---|---|---|---|---|---|
| 0 | 0.10 | 5.0 [4.0, 14.0] | 18.0 [17.0, 19.0] | 17.5 [15.0, 18.0] | 18.0 [16.0, 19.0] |
| 0 | 0.35 | 0.0 [0.0, 0.0] | 5.0 [5.0, 7.0] | 1.0 [1.0, 2.0] | 6.0 [5.0, 8.5] |
| 0 | 1.00 | 0.0 [0.0, 0.0] | 3.0 [3.0, 3.0] | 0.0 [0.0, 0.0] | 3.0 [3.0, 4.0] |
| 1 | 0.35 | 2.0 [1.0, 5.0] | 12.5 [8.0, 14.0] | 12.0 [10.0, 16.0] | 13.0 [11.0, 15.5] |
| 2.5 | 0.60 | 5.0 [5.0, 6.0] | 6.5 [6.0, 7.0] | 6.0 [6.0, 6.0] | 7.0 [6.0, 8.0] |
| 5 | 1.00 | 8.0 [8.0, 8.5] | 8.0 [8.0, 9.0] | 8.0 [8.0, 8.0] | 9.0 [8.0, 9.0] |

Median survival fraction over the whole grid: B0 **0.350** [0.300, 0.375],
B1 **0.650** [0.600, 0.700], B2 **0.450** [0.450, 0.525],
B3 **0.700** [0.650, 0.750].

### One sensor state is worth more than everything else on the capability axis

Going from S = 2 to S = 3 — being able to tell a pursuer from a robot — is the
whole story. The blind row is wiped out at κ = 0 for every range beyond 0.10 m;
any row that can see the pursuer keeps 3–18. Adding the memory bit on top (B3)
buys a further robot or two consistently, but nothing like as much.

### S = 5 scoring below S = 3 is a hand-design artefact, not a result

B2 has more sensor states than B1 and does worse over most of the grid — 0.450
against 0.650 median survival. **Its table is a hand-written guess (‡), and a bad
one.** It says no good five-state controller was found by hand; it is not
evidence about what five states can do, and it is not searched, so it is not even
an upper bound in the sense §7's rows are. Reporting it as "more sensing hurts"
would be the single easiest mistake to make with this data — the §7 experiment
shows exactly how that mistake gets made and what control prevents it.

### The environment dials dominate the capability rows

At κ = 5 the rows converge: every row keeps 8–9 robots at r_p = 1.0 and 18–19 at
r_p = 0.35. At κ = 0, r_p = 0.35 they run 0 to 6. Confusion and range move the
outcome more than any capability step does over the ranges swept — which §8 then
shows is *because* of aggregation rather than in spite of it.

Figure: `figures/pursuer_idea_b_surface.png`.

---

## 6. Idea A mechanism test: is it deformation, or just speed heterogeneity?

`configs/sweeps/terrain_mechanism.toml` — n = 20, τ = 600 s, 100 runs/cell,
**paired seeds**: both rows use the same swarm placements and the same traction
field, and differ only in how the field is sampled.

* **per-wheel** — each wheel samples at its own contact point. The corrected
  model, which changes curvature.
* **scalar-centre** — both wheels take one multiplier sampled at the robot's
  centre. This is v1's scalar speed field. It cannot change the turn radius:
  scaling both wheels by `m` gives `v' = mv` and `ω' = mω`, so `dp/dθ = v/ω` is
  independent of `m` and the robot traces the *same circle* at a
  position-dependent rate. (Pinned by
  `terrain::tests::a_scalar_centre_field_cannot_change_the_turn_radius`.)

The question the test settles: a scalar field still makes robots in different
places move at different rates, and that alone changes who meets whom. Is *that*
the mechanism, with curvature incidental?

**Decision rule, fixed before running:** if the scalar row reproduces the
per-wheel row's peak location and magnitude within CI, the mechanism is relative
speed heterogeneity and the curvature explanation is retired.

### It does not reproduce. The scalar field does nothing.

Degradation relative to each row's own θ_m = 0 cell, median [95% bootstrap CI]:

| λ | λ/R₀ | per-wheel, θ_m = 0.7 | scalar-centre, θ_m = 0.7 | per-wheel, θ_m = 0.9 | scalar-centre, θ_m = 0.9 |
|---|---|---|---|---|---|
| 0.0125 | 0.09 | 1.10 [1.06, 1.14] | 0.97 [0.96, 0.99] | 1.19 [1.11, 1.31] | 0.99 [0.97, 1.01] |
| 0.025 | 0.17 | 1.28 [1.19, 1.35] | 0.99 [0.98, 1.01] | 1.44 [1.39, 1.62] | 1.00 [0.99, 1.02] |
| 0.05 | 0.35 | 1.56 [1.44, 1.71] | 1.00 [0.98, 1.01] | 2.08 [1.84, 2.47] | 1.01 [0.99, 1.03] |
| **0.10** | **0.69** | **1.58 [1.48, 1.72]** | 0.96 [0.94, 0.98] | **2.21 [1.90, 2.41]** | 0.98 [0.96, 1.01] |
| 0.20 | 1.38 | 1.13 [1.09, 1.23] | 0.97 [0.94, 0.99] | 1.47 [1.32, 1.65] | 0.98 [0.97, 1.00] |
| 0.40 | 2.77 | 1.02 [1.00, 1.06] | 0.96 [0.94, 0.98] | 1.11 [1.06, 1.18] | 0.96 [0.94, 0.97]

Pooled over every θ_m > 0 cell (n = 1800 runs each):

* per-wheel **1.175 [1.154, 1.190]**
* scalar-centre **0.980 [0.976, 0.986]**

Neither the peak location nor the magnitude reproduces. The per-wheel row has a
peak at λ/R₀ = 0.69 rising to 2.21×; the scalar row has **no peak at all** — it
is flat within [0.96, 1.01] across the entire grid, and its CI excludes the
per-wheel value at every λ ≤ 0.2 for every θ_m ≥ 0.4.

**Per the decision rule, the curvature explanation stands and is not retired.**
Relative speed heterogeneity between robots is not sufficient to degrade
aggregation here; the per-wheel term is doing the work. This is a direct
vindication of the build doc's correction: v1's model would have measured
nothing, and the paper can now say so with a paired control rather than an
argument.

### One thing that differs, reported without explanation

The scalar row sits *slightly below* 1.0 — pooled 0.980 [0.976, 0.986], a CI
that excludes 1.0. A pure scalar speed field appears to aggregate marginally
*better* than flat ground, by about 2%.

The decision rule says report and stop, so that is all this says. It is not in
the direction H1 predicted (H1 is about small perturbations helping, and this is
across the whole θ_m range including the largest), and 2% is at the edge of what
this design resolves. Added to the "next" list rather than chased.

Figure: `figures/terrain_mechanism.png`.

### θ_m ceiling

The field reaches |f| = 1, so at θ_m = 1 the traction multiplier `1 + θ_m·f` can
reach zero and a wheel stalls outright — the robot pivots, which is a different
dynamical regime, not terrain deformation. All terrain sweeps from here are cut
at **θ_m = 0.9**, below the `1/max|f| = 1.0` where that becomes possible. A floor
of `m ≥ 0.05` is implemented as a safety net and is verified never to bind inside
the swept range (`terrain::tests::the_traction_floor_does_not_bind_in_the_swept_range`).

The θ_m = 1.25–1.5 band visible in the earlier H2 figure was stall, not terrain,
and has been removed from the swept range rather than explained away.

---

## 7. Idea A, H3: the first terrain-aware capability row

`configs/sweeps/terrain_h3_capability.toml` — n = 20, τ = 600 s, 100 runs/cell,
evaluated on seeds **disjoint** from the ones the searches trained on.

Three rows:

| row | c = (S, M, A, K) | constants | provenance |
|---|---|---|---|
| S2-gauci | (2, 0, 0, 0) | 4, Gauci's | enumerated — **tight** |
| S2-searched | (2, 0, 0, 0) | 4, re-searched | † |
| S4-terrain | (4, 0, 0, 0) | 8, binary LOS × terrain bit | † |

The terrain bit is `|m(x,y) − 1| > θ_bit` at the robot centre, with `θ_bit`
defaulting to the field median `θ_m · MEDIAN_ABS`. A bit that is almost always
the same value carries nothing, so the threshold is chosen to split ~50/50;
`terrain::tests::the_default_terrain_bit_is_informative` holds it between 0.4
and 0.6 across the amplitude range.

**S2-searched is why this experiment can be interpreted.** Without it, any S=4
advantage could just as well be "searched" rather than "more sensing". Both
searched rows got the same optimiser (sep-CMA-ES, diagonal covariance), the same
budget — **600 candidate evaluations × 12 runs = 7 200 simulation runs each** —
and the same training seeds, so the difference between them is the extra state
and nothing else.

### At the peak, the extra state does not buy back degradation. Search does.

Hold ratio at λ = 0.10 (λ/R₀ = 0.69, the H2 peak), median [95% CI]:

| θ_m | S2-gauci | S2-searched † | S4-terrain † |
|---|---|---|---|
| 0.0 | 1.00 [0.98, 1.03] | 1.00 [0.99, 1.02] | 1.00 [0.99, 1.01] |
| 0.4 | 1.13 [1.09, 1.17] | 0.96 [0.95, 0.97] | 1.00 [0.99, 1.01] |
| 0.6 | 1.36 [1.26, 1.48] | 0.99 [0.97, 1.01] | 1.02 [1.01, 1.04] |
| **0.9** | **2.21 [1.90, 2.41]** | **1.10 [1.08, 1.15]** | **1.22 [1.16, 1.26]** |

Re-searching the *same four constants* removes almost all of the degradation:
2.21 → 1.10 at the worst cell. Adding the terrain bit on top does not help — the
S=4 row sits at 1.22 [1.16, 1.26] against the S=2 searched row's 1.10 [1.08,
1.15], and those intervals are **disjoint**.

So the answer to "does the extra state buy back the peak?" is **no, at this
budget**, and the thing that does buy it back is searching four constants rather
than adding a fifth state's worth of sensing.

**What this does not say.** It does not say S = 4 is worse than S = 2. Both rows
are upper bounds, and they were given the same *total* budget over different
dimensionalities: 600 evaluations over 8 constants is a less thorough search per
dimension than 600 over 4. The honest statement is that **no S = 4 controller
better than the searched S = 2 one was found at equal budget.** Whether one
exists is open, and the way to settle it is a budget scaled with dimension, not
a stronger adjective.

Without the S2-searched control, this data would have read as "the terrain bit
cuts degradation from 2.21 to 1.22" — a large apparent win for extra sensing,
and wrong.

### Reach and hold answer different questions

Reach probability — the fraction of runs that ever formed a single cluster — is
1.00 across almost the whole grid. It only moves in the worst cell, and only for
the un-searched row: at λ = 0.10, θ_m = 0.9 it is 0.86 [0.79, 0.93] for S2-gauci
against 1.00 [1.00, 1.00] and 0.99 [0.97, 1.00] for the searched rows.

Terrain at n = 20 does not stop a swarm aggregating; it stops it holding
together tightly. A threshold `T` set on reach would see nothing over most of
this grid. Confirms §2's reading with a second design.

*(Reach is a proportion, and its median is 1 whenever the majority succeed, so
plotting a median draws a flat line at 1 while the probability falls. The panels
use `stats.proportion_ci`; the first version of this figure did not, and was
wrong.)*

### The search independently rediscovered H2

The searched controllers have much smaller state-0 circles than Gauci's:

| row | state-0 R₀ |
|---|---|
| S2-gauci | 14.45 cm |
| S2-searched | 4.7 cm |
| S4-terrain (smooth) | 6.8 cm |
| S4-terrain (rough) | 3.8 cm |

H2 says the terrain effect peaks at λ/R₀ ≈ 0.7 and vanishes for λ/R₀ ≳ 1.3. At
the training condition λ = 0.10 m, shrinking R₀ from 14.45 cm to 4.7 cm moves
λ/R₀ from 0.69 — the worst place to be — to 2.13, well clear of the peak. The
optimiser was given no information about R₀ or about H2; it found the escape H2
predicts. That is a consistency check between an independent measurement and a
search, not a new claim.

It also explains why the terrain bit adds so little here: the cheap defence
against a correlation length is to change your own length scale, and that is
available to the S = 2 row already. A terrain bit would have to earn its keep
doing something a smaller circle cannot.

**Caveat on the searched rows' baselines.** They also aggregate *tighter on flat
ground* — absolute dispersion at θ_m = 0 is 1.427 [1.399, 1.467] for S2-gauci,
1.253 [1.234, 1.283] for S2-searched and 1.222 [1.211, 1.235] for S4-terrain.
Part of what the search bought is a better controller in general, not a
terrain-specific one. The hold ratio normalises each row by its own flat
baseline precisely so this cannot be read as terrain robustness.

Figure: `figures/terrain_h3_capability.png`.

---

## 8. Idea B: is the blind row's survival actually attributable to aggregation?

`configs/sweeps/pursuer_dispersive.toml` — n = 20, τ = 120 s, ρ = 1.5, start
radius 0.74 m, **5 × 5 grid** of (r_p, κ) at two handling times, 100 runs/cell,
15 000 trials.

§5 found survival rising steeply with confusion and read it as dilution. But
every row there aggregated identically when no pursuer was in view, so nothing
distinguished *the swarm aggregated* from *the pursuer's perception is poor*.
This adds the missing control:

| row | sensing | spatial strategy | mark |
|---|---|---|---|
| B0-blind | S = 2, cannot see the pursuer | aggregates (Gauci) | tight |
| B1-ternary | S = 3, flees the pursuer | aggregates | ‡ |
| **D-dispersive** | S = 3, flees the pursuer | **does not aggregate** | ‡ |

D's state-0 is a 99 cm arc instead of Gauci's 14.45 cm circle, and its
robot-seen state is identical to it, so a robot never stops for a neighbour and
no cluster forms. Its pursuer response is byte-identical to B1's. The only
difference between B1 and D is the spatial strategy.

Handling times come from the pursuer's own travel time between touching
neighbours in a formed cluster — 7.4 cm at ρ·v_max = 19.2 cm/s is 0.385 s — so
h = 0.39 s is comparable to it and h = 1.93 s is 5×.

### Yes. Confusion acts through aggregation, and the control proves it.

Mean survival fraction over the whole grid, κ = 0 → κ = 5:

| row | h = 0.39 | h = 1.93 |
|---|---|---|
| B0-blind | 0.180 → 0.548 (**×3.05**) | 0.144 → 0.592 (**×4.10**) |
| B1-ternary ‡ | 0.258 → 0.575 (×2.23) | 0.328 → 0.628 (×1.91) |
| D-dispersive ‡ | 0.530 → 0.638 (×1.20) | 0.591 → 0.666 (**×1.13**) |

The two aggregating rows multiply their survival by 2–4× as confusion rises. The
dispersive row, with identical pursuer sensing, gains 13–20%. Confusion enters
the model only through `p_lock = 1/(1 + κ·n_local)`, and only a clustered swarm
has a large `n_local`, so this is the mechanism doing exactly what it is written
to do — but it had not been *shown* before, because nothing separated it from
the pursuer simply being worse at its job.

Handling time sharpens it in the predicted direction: B0's κ-response grows from
×3.05 to ×4.10 when handling goes from comparable to the inter-neighbour travel
time to 5× it, while D's shrinks slightly. Dilution needs the predator to be
busy; making it busier makes clustering pay more.

### But aggregation is still a net liability over this grid

Survival pooled over κ, at h = 1.93:

| r_p | B0-blind | B1-ternary ‡ | D-dispersive ‡ |
|---|---|---|---|
| 0.10 | 0.90 [0.90, 0.95] | 0.95 [0.95, 0.95] | 0.90 [0.85, 0.90] |
| 0.20 | 0.85 [0.80, 0.85] | 0.85 [0.85, 0.90] | 0.75 [0.75, 0.78] |
| 0.35 | 0.00 [0.00, 0.23] | 0.55 [0.45, 0.65] | 0.65 [0.60, 0.65] |
| 0.60 | 0.00 [0.00, 0.00] | 0.05 [0.05, 0.05] | 0.50 [0.45, 0.50] |
| 1.00 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.35 [0.30, 0.35] |

Whenever the pursuer's range exceeds ~0.35 m the dispersive row wins, and by a
lot. Confusion narrows the gap — mean survival at κ = 5 is 0.592 (B0), 0.628
(B1), 0.666 (D) — but does not close it. Over this grid, clustering never
becomes the better bet on average; it only stops being catastrophic.

That is a sharper version of the build doc's own warning. The doc fixed v1 by
giving the pursuer perception limits so that aggregation *could* protect. It can,
in the sense that confusion helps it far more than it helps dispersal — and it
still loses to simply not being in one place, unless the pursuer's range is short
enough that nothing is found anyway.

### Saturation, stated rather than hidden

29% of all runs ended with the swarm wiped out, and `survival_fraction` is pinned
at 0 there. It is concentrated exactly where the claim is strongest — B0 loses
the whole swarm in 72% of runs at κ = 0, falling to 27% at κ = 5, while D wipes
out in ≤ 1% anywhere.

Time to wipeout is the readable measure in those cells (r_p = 0.35, h = 1.93):

| κ | B0-blind | B1-ternary ‡ | D-dispersive ‡ |
|---|---|---|---|
| 0.0 | 46.6 s (n = 94) | 70.2 s (n = 19) | never |
| 1.0 | 64.4 s (n = 71) | 82.6 s (n = 26) | never |
| 2.5 | 88.8 s (n = 8) | 102.4 s (n = 3) | never |
| 5.0 | never | never | never |

Same story, unsaturated: confusion buys the aggregating rows time, and the
dispersive row never needs it.

### What these rows cannot say

B1 and D are **hand-designed (‡), not searched**. They support a claim about
*spatial strategy* — which is what they were built to isolate, and D differs from
B1 in exactly one respect — but nothing they show is evidence about what S = 3
sensing can achieve. The S = 5 result in §5 stays labelled ‡ for the same reason.

Figures: `figures/pursuer_dispersive_kappa.png`,
`figures/pursuer_dispersive_surface.png`.

---

---

## 9. Does re-tuning move the problem or solve it?

`configs/sweeps/terrain_retune_cost.toml` — λ = 0.10 m (λ/R₀ = 0.69) fixed, θ_m
swept 0 → 0.9 in eight steps, n = 20, τ = 600 s, 100 runs/cell, base seeds
20260904 as in the H2 and H3 sweeps.

S2-searched was tuned at exactly one point: the worst cell H2 found. A controller
tuned at the worst cell can win there by giving up performance everywhere else,
and §7 only ever evaluated it on terrain. If such a trade-off exists, the terrain
bit has an obvious job — switch between the two controllers — and the
**S4-composite** row is that switch, built by hand: `terrain-bit = 0` takes
Gauci's four constants, `terrain-bit = 1` takes S2-searched's. It is
hand-designed (‡), so it is evidence about this arrangement, not about S = 4.

### The decision rule fired neither branch

The rule anticipated two outcomes at θ_m = 0: S2-searched *matches* Gauci within
CI, or S2-searched is *worse* with disjoint CIs. Measured, absolute final
dispersion at θ_m = 0:

| row | dispersion at θ_m = 0 |
|---|---|
| S2-gauci | 1.427 [1.399, 1.467] |
| S2-searched † | **1.253 [1.234, 1.283]** |

The intervals are disjoint and S2-searched is **strictly better** — 12.2% lower —
on the flat ground it was never tuned for. There is no trade-off to report.

And it is not a flat-ground artefact. S2-searched beats S2-gauci with **disjoint
CIs at every one of the eight θ_m values**:

| θ_m | S2-gauci | S2-searched † | S4-composite ‡ | S4-searched † |
|---|---|---|---|---|
| 0.00 | 1.427 [1.399, 1.467] | 1.253 [1.234, 1.283] | 1.427 [1.399, 1.467] | 1.222 [1.211, 1.235] |
| 0.30 | 1.521 [1.470, 1.568] | 1.211 [1.199, 1.226] | 1.476 [1.424, 1.527] | 1.219 [1.210, 1.230] |
| 0.60 | 1.943 [1.799, 2.112] | 1.235 [1.220, 1.264] | 1.638 [1.562, 1.783] | 1.248 [1.239, 1.268] |
| 0.90 | **3.150 [2.716, 3.439]** | **1.383 [1.350, 1.441]** | 1.999 [1.861, 2.143] | 1.486 [1.424, 1.535] |

Reach probability (Wilson 95%) says the same at the hard end: S2-gauci drops to
**0.86 [0.78, 0.91]** at θ_m = 0.9 while S2-searched stays at 1.00 [0.96, 1.00].

**Re-tuning solves the problem. It does not move it.**

### So the frontier is flat in capability along this dial

Since one four-constant controller dominates the other everywhere, there is
nothing for a terrain bit to switch between, and the composite demonstrates that
constructively rather than by argument: it is **worse than the S = 2 row it is
built from at every θ_m** — 1.999 against 1.383 at θ_m = 0.9 — because half the
time it deliberately selects the worse of its two behaviours.

Its θ_m = 0 value is 1.427 [1.399, 1.467], identical to Gauci's, which is the
internal consistency check: on flat ground the terrain bit is never set, so the
composite *is* Gauci, and it reproduces its number exactly.

`c*(θ_terr)` is **flat in capability** over 0 ≤ θ_m ≤ 0.9 at λ/R₀ = 0.69:
`c = (2, 0, 0, 0)` suffices at every point, and the minimum does not move.

That is a negative result for H3 and a real one for the project's central
question. The build doc's programme is to measure how the capability minimum
moves under hostility; along this dial, over this range, **it does not move at
all — what moves is the parameter setting inside a fixed capability.** Capability
and parameters are different axes, and only one of them responded.

### The caveat that has to travel with this

S2-searched beating Gauci *on flat ground* is a statement about **this
simulator's objective**, not a claim that Gauci's exhaustive grid search was
wrong. Their search was exhaustive at its resolution on their metric and setup;
this one optimises median final dispersion at n = 20, τ = 600 s under this
repository's dispersion normalisation, collision model and cluster definition.
Two different objectives have two different optima, and the derived-values test
(R₀ = 14.45 cm, ω₀ = 0.75, ω₁ = 5.02 rad/s) confirms the *reproduction* is
faithful regardless.

What this does mean is that any claim of the form "capability X is needed at
hostility θ" in this project must be checked against a re-search of the cheaper
capability first. §7 already showed that; this shows the re-search need not even
cost anything elsewhere.

### Limitations

* One λ. The dominance is established at λ/R₀ = 0.69 only. A controller with a
  4.7 cm circle may be worse at a correlation length matched to *its* R₀ — that
  is what H2 would predict, and it is on the next list rather than run here.
* Both S = 4 rows remain upper bounds; the composite is not even that, being
  hand-built.
* Everything is n = 20.

Figure: `figures/terrain_retune_cost.png`.

---

## 10. Warm-started S = 4 search

`configs/sweeps/terrain_warm_s4.toml`, from `results/search_s4_warm.json`.

§7's result — no S = 4 controller better than the searched S = 2 one — carried an
obvious objection: equal *total* budget over 8 constants is a thinner search per
dimension than over 4, so the S = 4 row might have lost on search effort rather
than on capability. This removes the **direction** of that confound.

The search starts at `[S2-searched | S2-searched]`: an eight-constant table whose
two halves are equal, which is an S = 4 controller that ignores its own terrain
bit and behaves exactly like the S = 2 controller achieving 1.10 at the peak. The
optimiser therefore begins holding the S = 2 optimum, and the only question it
can be asked is whether *using* the bit beats *not* using it. Same optimiser,
same budget (600 evaluations × 12 runs = 7 200 simulation runs), training seeds
950 000 — disjoint from the cold search's 900 000 and from the evaluation seeds.

The search did move: L2 distance 0.464 from its start, and the two halves
diverged by up to 0.254, so the found controller genuinely uses the bit.

### It ties, and does not beat, the S = 2 row it started from

Absolute final dispersion on held-out seeds:

| θ_m | S2-searched † | S4-searched † (cold) | S4-warm † |
|---|---|---|---|
| 0.00 | 1.253 [1.234, 1.283] | 1.222 [1.211, 1.235] | 1.216 [1.204, 1.226] |
| 0.45 | 1.212 [1.201, 1.222] | 1.212 [1.205, 1.224] | 1.218 [1.203, 1.227] |
| 0.75 | 1.322 [1.280, 1.358] | 1.330 [1.288, 1.366] | 1.297 [1.273, 1.340] |
| **0.90** | **1.383 [1.350, 1.441]** | 1.486 [1.424, 1.535] | **1.412 [1.349, 1.503]** |

At the peak cell — the cell both searches trained on — S4-warm is
**1.412 [1.349, 1.503]** against S2-searched's **1.383 [1.350, 1.441]**. The
intervals **overlap**; the point estimate is 2.1% *worse*. Given the S = 2
optimum as a starting point and an equal budget, using the terrain bit did not
improve on ignoring it.

The warm start does help relative to the cold S = 4 search at the peak (1.412
against 1.486), which is what a better starting point should do. It just does not
get past S = 2.

### Why the disjoint-seed protocol earns its keep here

The warm search's *training* objective was **1.2595**, better than the cold
search's 1.3012 and than the S = 2 search's 1.3009. On held-out seeds that
advantage disappears. The training objective is the minimum of a noisy sample —
12 runs per candidate over 600 candidates — so the best-looking candidate is
partly the luckiest one. Reporting it would have shown a warm-start "win" that
does not exist.

### Limitations

* **Equal budget across unequal dimensions still applies.** Eight dimensions
  still receive the same total evaluations as four. What the warm start rules out
  is the specific objection that the S = 4 row never had access to the S = 2
  optimum — it started there.
* sep-CMA-ES is diagonal-only and not exhaustive; the row stays an upper bound
  (†). A stronger searcher could still find something.
* One λ, one training cell, n = 20.

Figure: `figures/terrain_warm_s4.png`.

---

## 11. Validating the gradient-steering mechanism

`configs/sweeps/terrain_mechanism_regression.toml` — θ_m = 0.9, λ = 0.10 m
(λ/R₀ = 0.69 for the base row), 100 runs/cell, **12 million robot-timesteps
pooled per row**. Accumulated as OLS sufficient statistics rather than stored
rows; they add across runs, so a sweep pools by summing.

§§4 and 6 established *where* the terrain effect is and that a scalar speed field
does not produce it. Neither measured the proposed mechanism. This regresses the
per-timestep heading-rate residual against the field gradient across the axle.

### The algebra first, because it decides what to regress

With slope = 0, the residual is exactly

```
residual = ω_actual − ω_commanded
         = v·(m_R − m_L)/ℓ  +  (ω/2)·(m_R + m_L − 2)
```

and to first order about the robot centre, with `n̂` running from the left wheel
contact to the right,

```
residual  =  v·∂m/∂n   +   ω·(m(centre) − 1)
             ⌞ gradient ⌟   ⌞ mean-traction ⌟
```

Both terms are the **same per-wheel traction mechanism**: the first is the wheels
seeing different ground, the second is a turning robot on ground uniformly slower
than nominal. This is arithmetic, verified to six decimals against the simulator,
not a second hypothesis.

It matters because the two terms are built from the same field and are therefore
**correlated**, so regressing on the gradient term alone gives a *biased* slope,
not merely a noisy one. Both fits are reported.

`∂m/∂n` is differenced from the **field at the robot centre**, never from the two
wheel samples — the wheel difference is what the residual is made of, so
regressing on it would be an identity.

### Result: slope → 1, and it degrades exactly as ℓ/λ → 1

| row | axle | **ℓ/λ** | R₀ | full slope | full R² | gradient-only slope | gradient-only R² |
|---|---|---|---|---|---|---|---|
| axle-half-R0-same ‡ | 2.55 cm | **0.25** | 14.45 cm | **0.976** | **0.9983** | 0.522 | 0.0215 |
| base | 5.10 cm | **0.51** | 14.45 cm | 0.900 | 0.9738 | 0.681 | 0.1367 |
| R0-half-axle-same ‡ | 5.10 cm | **0.51** | 7.22 cm | 0.894 | 0.9719 | 0.652 | 0.0924 |
| R0-x2-axle-same ‡ | 5.10 cm | **0.51** | 28.90 cm | 0.901 | 0.9760 | 0.809 | 0.2408 |
| axle-x2-R0-same ‡ | 10.20 cm | **1.02** | 14.45 cm | **0.623** | **0.7373** | 0.539 | 0.2776 |

Three things, all as predicted:

1. **Slope 0.976 with R² 0.998** at the narrowest axle. The residual *is* the
   first-order per-wheel traction effect; there is essentially nothing else in it.
2. **Both fall monotonically with ℓ/λ** — slope 0.976 → 0.900 → 0.623, R² 0.998 →
   0.974 → 0.737 — and the fall is steepest past ℓ/λ = 1, exactly where a
   first-order expansion about the centre stops describing what the wheels see.
3. **The control works.** The three rows at ℓ/λ = 0.51 span a **4× range of R₀**
   (7.22, 14.45, 28.90 cm) and agree to **0.007 in slope** and 0.004 in R². ℓ/λ
   decides the quality of the linearisation; R₀ does not touch it.

Point 3 is worth separating from §4's result. R₀ sets *where the terrain effect
peaks* — that is the swarm-level finding. ℓ/λ sets *how well a first-order
expansion describes a single robot's turn rate* — that is this one. They are
different questions about different objects, and the same sweep answers both
because the rows were built to vary the two independently.

### The gradient-only regression, as literally specified

Slopes 0.52–0.81, R² 0.02–0.28 — nowhere near 1, at any ℓ/λ. That is the
predicted consequence of omitting a correlated term, and its size is set by how
large ω·(m̄ − 1) is relative to v·∂m/∂n: at these constants the mean-traction term
is roughly ten times the gradient term, so it dominates both the variance and the
bias. Reported, and stopped there — no third mechanism is proposed, because the
decomposition above accounts for the discrepancy exactly.

### Limitations

* One θ_m, one λ. The ℓ/λ trend is established across three axle values at a
  single correlation length; whether it collapses on ℓ/λ across λ as well is
  untested and is on the next list.
* Four of the five rows are hand-picked constants (‡). That mark is about how the
  constants were obtained; nothing here is a minimality claim.
* `axle-x2-R0-same` puts the wheel contacts outside the 7.4 cm body — a numerical
  device, not a buildable robot, and it is the row carrying the ℓ/λ ≈ 1 point.

Figure: `figures/terrain_mechanism_regression.png`
(regenerate with `harness/figures_mechanism_regression.py`).

---

## 12. Idea B Pareto front: what survival costs

`configs/sweeps/pursuer_pareto.toml` — five rows at h = 1.93 s, ρ = 1.5, n = 20,
τ = 120 s, start radius 0.74 m, 100 runs/cell.

Every earlier Idea B figure scored survival alone, which cannot see what
surviving cost. `final_dispersion` is already computed over *surviving* robots in
the centroid frame, so plotting both coordinates gives the trade-off directly.

**D-dispersive is the task-abandoning end of the front, not a competitor
controller.** It is included to show where the trade-off terminates; reading it
as "the best row" would treat the axis it gives up as free.

The base-task axis is dropped below three survivors: with one or zero survivors
the dispersion of "the survivors" is 0, a perfect aggregation score for a swarm
that has been wiped out. Runs kept per cell are reported.

### The three cells

| cell | row | survival at τ | dispersion (survivors ≥ 3) | runs kept | wiped out | median t_wipeout |
|---|---|---|---|---|---|---|
| **r_p = 0.2, κ = 0** | B0-blind | 0.000 [0.000, 0.000] | 1.426 [1.363, 1.497] | 23 | 72% | 47.1 s |
| | B1-ternary ‡ | 0.475 [0.200, 0.750] | 1.630 [1.510, 1.787] | 68 | 12% | 81.0 s |
| | B2-ternary-side ‡ | 0.150 [0.100, 0.275] | 1.443 [1.417, 1.560] | 52 | 21% | 63.8 s |
| | B3-ternary-memory ‡ | 0.650 [0.400, 0.800] | 1.597 [1.538, 1.749] | 79 | 1% | 109.8 s |
| | **D-dispersive ‡** | **0.750 [0.675, 0.750]** | **379.9 [344.3, 399.9]** | 100 | 0% | — |
| **r_p = 0.35, κ = 3** | B0-blind | 0.800 [0.750, 0.850] | 1.451 [1.412, 1.501] | 97 | 2% | 91.4 s |
| | B1-ternary ‡ | 0.800 [0.800, 0.850] | 1.508 [1.461, 1.573] | 98 | 2% | 106.5 s |
| | B2-ternary-side ‡ | 0.850 [0.800, 0.850] | 1.502 [1.445, 1.558] | 98 | 2% | 91.5 s |
| | B3-ternary-memory ‡ | 0.800 [0.800, 0.850] | 1.523 [1.484, 1.575] | 97 | 0% | — |
| | **D-dispersive ‡** | 0.650 [0.600, 0.700] | 386.3 [357.9, 431.3] | 100 | 0% | — |
| **r_p = 1.0, κ = 3** | B0-blind | 0.000 [0.000, 0.000] | not estimable (1/100) | 1 | 96% | 97.6 s |
| | B1-ternary ‡ | 0.000 [0.000, 0.000] | 10.3 [6.8, 15.1] | 12 | 66% | 107.9 s |
| | B2-ternary-side ‡ | 0.000 [0.000, 0.000] | not estimable (4/100) | 4 | 90% | 103.6 s |
| | B3-ternary-memory ‡ | 0.000 [0.000, 0.000] | not estimable (9/100) | 9 | 66% | 105.3 s |
| | **D-dispersive ‡** | **0.350 [0.325, 0.400]** | **504.8 [432.9, 613.9]** | 94 | 0% | — |

### The cost is two orders of magnitude, and it is not always worth paying

D's dispersion is **380–505** against **1.43–1.63** for every aggregating row.
That is the price of its survival, stated in the units of the task the swarm
exists to perform. Survival-only figures make D look like the best row; on both
axes it is a different animal.

**At r_p = 0.35, κ = 3 there is no trade-off at all.** Every aggregating row
beats D on *both* coordinates — survival 0.80–0.85 against 0.65, dispersion
~1.5 against 386. D is Pareto-dominated. This is the regime where confusion has
made clustering safe (§8) and clustering is also what the task wants, so nothing
is given up.

**At the other two cells the trade-off is real.** At r_p = 0.2, κ = 0 D has the
highest survival (0.750) and the worst task performance by 250×. At r_p = 1.0,
κ = 3 D is the only row that survives at all, and the aggregating rows are wiped
out in 66–96% of runs.

### Where survival saturates, timing still separates the rows

Both cells with median survival 0.000 would be indistinguishable on a survival
axis alone. Time to wipeout is not: at r_p = 0.2, κ = 0 it runs 47.1 s (B0),
63.8 s (B2), 81.0 s (B1), 109.8 s (B3) — the same ordering the survival medians
show at the unsaturated cells, recovered where they are pinned.

### Limitations

* Four of five rows are hand-designed (‡). The front is between *spatial
  strategies* and specific tables, not between capabilities. B0 is enumerated and
  is the only row here whose constants are not a guess.
* At r_p = 1.0, κ = 3 the base-task axis is not estimable for three of the four
  aggregating rows — too few runs leave three survivors. The panel says so rather
  than plotting an interval built from one or four runs.
* One handling time, one ρ, one n, one τ.

Figure: `figures/pursuer_pareto.png`
(regenerate with `harness/figures_pareto.py`).

---

## 13. The 2×2 tuning control: how much of §9 was terrain?

`configs/sweeps/terrain_tuning_control.toml` — λ = 0.10 m (λ/R₀(gauci) = 0.69),
θ_m swept 0 → 0.9 in eight steps, n = 20, τ = 600 s, 100 runs/cell, evaluation
seeds 20260904 as in §9.

§9 concluded "re-tuning solves it", and that conflated two things. S2-rough
(§7–§10's "S2-searched", renamed here) was tuned against **this objective** —
median final dispersion at n = 20, τ = 600 s, start radius 0.74 m, under this
repository's normalisation and collision model — while Gauci's constants were
found for a different one. "Tuned for this objective" and "tuned for terrain"
were not separated.

**S2-flat** is the missing cell: same optimiser, same budget (600 evaluations ×
12 runs), **same training seed base (900 000)**, differing from S2-rough only in
the θ_m of its training condition. Both are disjoint from the evaluation seeds.

### The three controllers

| row | state | constants | R₀ | forward speed | rotation rate |
|---|---|---|---|---|---|
| S2-gauci | 0 (blind) | (−0.7000, −1.0000) | 14.45 cm | −10.88 cm/s | −0.753 rad/s |
| | 1 (seen) | (+1.0000, −1.0000) | 0 (spin) | 0 | −5.020 rad/s |
| S2-flat † | 0 (blind) | (−0.3289, −0.8923) | 5.53 cm | −7.82 cm/s | −1.414 rad/s |
| | 1 (seen) | (+0.9983, −0.6589) | 0.52 cm | +2.17 cm/s | −4.159 rad/s |
| S2-rough † | 0 (blind) | (−0.2852, −0.9495) | 4.74 cm | −7.90 cm/s | −1.667 rad/s |
| | 1 (seen) | (+0.9354, −0.2262) | 1.56 cm | +4.54 cm/s | −2.915 rad/s |

L2 distances: **S2-flat ↔ S2-rough 0.443**, S2-flat ↔ S2-gauci 0.516,
S2-rough ↔ S2-gauci 0.882. The two searched controllers are closer to each other
than either is to Gauci, and *both* shrink the state-0 circle from 14.45 cm to
about 5 cm — the one trained on flat ground did so without ever seeing terrain.

### The decision rule: branch (c). They cross.

Because both rows share a seed base, run index *i* is the same initial placement
and the same traction field in both, so the difference can be taken run by run:

| θ_m | paired median (S2-flat − S2-rough) | 95% CI | verdict |
|---|---|---|---|
| 0.00 | −0.0596 | [−0.0763, −0.0371] | **flat better** |
| 0.10 | −0.0424 | [−0.0692, −0.0280] | **flat better** |
| 0.20 | −0.0359 | [−0.0482, −0.0172] | **flat better** |
| 0.30 | −0.0014 | [−0.0125, +0.0129] | no difference |
| 0.45 | +0.0089 | [−0.0176, +0.0219] | no difference |
| 0.60 | +0.0421 | [+0.0107, +0.0659] | **rough better** |
| 0.75 | +0.0273 | [−0.0160, +0.0658] | no difference |
| 0.90 | +0.0818 | [−0.0008, +0.1331] | no difference |

The sign flips between θ_m = 0.30 and 0.45, and the effect is **significant on
both sides** — flat wins at θ_m ≤ 0.2, rough wins at θ_m = 0.6. That is branch
(c): a trade-off exists, crossing at **θ_m ≈ 0.3–0.45**.

### But it is a 3% trade-off inside a 97% effect

Decomposing the Gauci → S2-rough gap at θ_m = 0.9 (absolute dispersion):

| | value | share of the gap |
|---|---|---|
| S2-gauci | 3.150 | |
| S2-flat † | 1.438 | **96.9% — objective-tuning** |
| S2-rough † | 1.383 | **3.1% — terrain-tuning** |

And on flat ground the terrain-tuning term *reverses*: S2-rough costs 4.1%
against S2-flat there. So terrain-tuning is worth about ±4% of dispersion in
either direction, while tuning for this objective at all is worth 119%.

Hold ratio at θ_m = 0.9, each row against its own flat baseline: S2-gauci
**2.208 [1.904, 2.410]**, S2-flat **1.195 [1.146, 1.265]**, S2-rough
**1.104 [1.078, 1.150]**. A controller that never saw terrain degrades by 20%
where Gauci's degrades by 121%.

### What this does to §9 and to correction #11

**§9's headline was right about the direction and wrong about the cause.**
Re-tuning does recover almost all of the loss, but not because it adapts to
terrain — because Gauci's constants are badly matched to *this objective*, and a
controller matched to it is far more terrain-robust as a side effect.

Two consequences:

1. **The H2 degradation curve is largely a property of Gauci's specific
   constants, not of terrain sensitivity in general.** At λ/R₀(gauci) = 0.69 a
   controller tuned only for this objective degrades 1.195× where Gauci's
   degrades 2.208×. The dial still bites — 1.195 is not 1.0 — but the published
   figure of ~2.2× overstates what terrain does to a well-matched controller by
   about a factor of six.
2. **The terrain bit is reopened, at the right pair.** §9's composite switched
   Gauci ↔ S2-rough, which the decomposition now shows was the wrong pair: most
   of that difference was objective-tuning, which a terrain bit cannot supply.
   The pair with a genuine crossing is **S2-flat ↔ S2-rough**, and a composite
   over those two is worth at most the ±4% the crossing spans. On the next list,
   not run here.

### Limitations

* One λ, one n, one start radius, one τ. Experiment 2 tests whether the searched
  rows' advantage survives outside the initial condition they were tuned in.
* Both searched rows are upper bounds (†) from a diagonal-covariance optimiser at
  a fixed budget.
* The crossing is located to θ_m ∈ [0.3, 0.45] by a sign flip in point estimates;
  the CIs at 0.30 and 0.45 both include zero, so a finer grid would be needed to
  pin it.

Figure: `figures/terrain_tuning_control.png`
(regenerate with `harness/figures_tuning_control.py`).

## Next (noted, not run)

Carried forward and updated. Items 1, 2 and 3 from the previous list are now
answered (§§6, 10, 12); what remains, plus what these four experiments surfaced:

1. **Does S2-searched hold up at a λ matched to its own R₀?** §9 establishes
   dominance at λ/R₀ = 0.69 for Gauci's R₀ = 14.45 cm. The searched controller has
   R₀ = 4.7 cm, so H2 predicts *its* worst correlation length is near λ = 3.3 cm,
   which this sweep never visits. If the terrain effect simply followed the
   controller down, "re-tuning solves it" would need qualifying.
2. **ℓ/λ across more than one λ.** §11's trend is three axle values at a single
   correlation length. Whether slope and R² collapse on ℓ/λ when λ varies too is
   the obvious completion, and it is one sweep.
3. **The scalar-field row's ~2% improvement** (§6), pooled 0.980 [0.976, 0.986].
   Still unexplained, still small, still a real interval.
4. **A searched dispersive row.** §12's front is between hand-designed spatial
   strategies. Searching both ends would say whether the front is a property of
   the strategies or of two guesses.
5. **Where the D-vs-aggregating crossover sits in r_p.** §12 brackets it between
   0.2 and 0.35 m at κ = 3; a denser r_p axis would locate it.
6. **Row B4** — the received alarm bit — still needs communication wired, and the
   delivery model (broadcast radius vs line-of-sight) is itself a capability
   claim to be counted in `K`.
7. **Budget scaled with dimension**, as opposed to a warm start. §10 removed the
   direction of the equal-budget confound; scaling the budget would remove it.
