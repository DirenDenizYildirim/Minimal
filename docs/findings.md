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

At θ_m = 1.5 every row degrades 6–14×, and the ordering by R₀ collapses. The
traction multiplier clamps at zero there, so wheels stall outright and the
dynamics are dominated by stalling rather than by deformation. Report θ_m ≤ 1.0
as the terrain regime and 1.5 as its boundary.

One row is not a robot at all: `axle-x2-R0-same` puts the wheel contacts outside
the 7.4 cm body. It exists to break the R₀/axle confound numerically, and no
result from it describes a buildable machine. It is what makes the 5% spread
above meaningful, and it should be described that way in the paper rather than
quietly included.

Figure: `figures/terrain_h2_powered.png`.

### What this leaves for the anisotropy lemma

The build doc wants a theorem of the form "aggregation holds if the anisotropy
ratio is below f(R₀, sensor range)". The measurement now says what f should
depend on: R₀ and the terrain correlation length, in the ratio λ/R₀, with the
worst case near 0.7. That is a much narrower target than the sweep started with,
and it is the natural next piece of analysis.

---

## 5. Idea B, first pass: the pursuer with imperfect perception

`configs/sweeps/pursuer_idea_b.toml` — n = 20, **τ = 120 s**, 100 runs/cell,
ρ = 1.5, handling time 5 s, four capability rows against a grid of `r_p` × `κ`.

**Rows B0–B3 only.** B4 needs a received alarm bit and communication is not
wired — `rx` is held at 0, so a K = 1 row would silently behave as K = 0.
B1–B3 are **hand-designed, not searched**: every number below is an upper bound
on what that capability can do.

### Median survivors out of 20

| κ | r_p | B0 blind | B1 ternary | B2 ternary+side | B3 ternary+memory |
|---|---|---|---|---|---|
| 0 | 0.2 | **0.0** | 15.5 | 10.5 | **17.0** |
| 0 | 0.5 | 0.0 | 4.0 | 1.0 | 4.5 |
| 0 | ∞ | 0.0 | 3.0 | 0.0 | 3.0 |
| 1 | 0.2 | 16.5 | 17.5 | 18.0 | 18.0 |
| 1 | 0.5 | 1.0 | 4.0 | 3.0 | 5.0 |
| 5 | 0.5 | 13.5 | 15.0 | 15.0 | 16.0 |
| 5 | ∞ | 8.0 | 8.0 | 8.0 | 8.0 |

### One sensor state is worth more than everything else on the capability axis

Going from S = 2 to S = 3 — being able to tell a pursuer from a robot — is the
whole story. The blind row loses every robot at κ = 0 whatever the pursuer's
range; any row that can see the pursuer keeps 3–17. Adding the memory bit on top
(B3) buys a further robot or two consistently but nothing like as much.

Median survival fraction over the whole grid: B0 0.10, B1 0.35, B2 0.20,
B3 0.375.

### S = 5 scoring below S = 3 is an upper-bound artefact, not a result

B2 has more sensor states than B1 and does worse almost everywhere — 10.5
survivors against 15.5 at the easiest cell. That is exactly what the build doc's
"minima are upper bounds" rule is for. B2's table is a hand-written guess at what
to do with side information, and a bad one; **it says no good five-state
controller was found, not that five states cannot beat three.** Reporting it as
"more sensing hurts" would be the single easiest mistake to make with this data.

This is also a concrete argument for Idea C: the rows most in need of a search
are the ones whose hand-designed controllers look worst.

### The environment dial dominates the capability rows

At κ = 5, r_p = ∞ every row scores 8 survivors — the capability differences
vanish entirely. At r_p = 0.2, κ = 5 every row keeps 19. Confusion and range
move the outcome far more than any capability step does, over the ranges swept.

That is the frontier the project is after, stated the other way round: for much
of this environment grid, `c*(θ)` is flat, and the interesting structure is
confined to the corner where the pursuer is dangerous and the swarm is not
already saved by its perception limits.

### Three design problems this pass exposed

1. **The metric saturates.** 13% of runs lost the whole swarm, mostly in B0, and
   `capture_rate` is pinned at 1/τ once that happens. τ = 120 s was chosen from a
   calibration probe and is still too long for the blind row. Either use
   `time_to_wipeout` for the lethal cells, or set τ per row, and say which.
2. **Range saturates too.** r_p = 1.0 and r_p = ∞ are identical in every cell,
   because a 20-robot swarm is inside 1 m anyway. The useful range dial is
   0.1–0.5 m; anything above is the same corner twice.
3. **This sweep cannot answer the headline question.** "Does aggregation protect
   the swarm?" needs aggregating and non-aggregating controllers compared under
   the same pursuer. All four rows here aggregate identically when no pursuer is
   in view, so the comparison is between *responses* to a pursuer, not between
   spatial strategies. Add a deliberately dispersive row — the same table with
   the state-1 rotation replaced by something that spreads — and the dilution
   question becomes answerable.

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
