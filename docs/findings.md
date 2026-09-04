# Findings so far

Experimental results, as distinct from `docs/validation.md`, which records
whether the simulator can be trusted.

**Read the caveat first.** The week-1 gate has not passed. Everything below is
at n = 20, where the open gate item (the sensor's field of view) changes results
only marginally — median final dispersion moves from 1.41 to 1.17 across the
entire plausible range of that parameter, against effect sizes here of 1.4 → 30.
So the *directions* below are robust and the *absolute numbers* are provisional.
Nothing here should be written up before the gate closes.

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

Median final dispersion (lower is more aggregated; the clean baseline is 1.40):

| false-negative rate | M0 (tight) | M1 hysteresis (upper bound) |
|---|---|---|
| 0.0 | 1.40 | 1.28 |
| 0.2 | 1.47 | 1.35 |
| 0.4 | 1.56 | 1.42 |
| 0.6 | 1.75 | 1.48 |
| 0.8 | 2.37 | 1.99 |
| 0.9 | 3.52 | 2.84 |

One bit buys a consistent improvement, including in the *clean* arena, and the
gap widens with the dropout rate. That is the answer the shakedown was for: the
eight-constant search is worth running.

### Spatially correlated dropout is worse — but mostly for a boring reason

At the same *nominal* rate, correlated dropout looks dramatically worse than
i.i.d.: at a nominal 0.6, dispersion is 3.83 correlated against 1.75 i.i.d.

It is largely an artefact of the nominal rate not being the realised one. The
correlated field is sampled where the robots actually are, and once a cluster
settles into a bad patch its readings are drawn from that patch, not from the
spatial average. The realised rate at a nominal 0.6 is **0.89**.

Binned by *realised* rate, most of the effect disappears (M0 row):

| realised FN rate | i.i.d. | correlated |
|---|---|---|
| 0.00–0.05 | 1.40 | 1.40 |
| 0.25–0.35 | 1.51 | 1.54 |
| 0.45–0.55 | 1.64 | 1.68 |
| 0.60–0.70 | 1.85 | 1.78 |
| 0.72–0.80 | 2.26 | 2.33 |
| 0.85–0.95 | 3.52 | **5.93** |
| 0.95–1.00 | — | 27.58 |

Below a realised rate of ~0.8 the two are indistinguishable. A genuine extra
penalty for spatial structure appears only above that, where the swarm can get
trapped in a patch that is effectively blind.

**Consequence for the write-up:** correlated and i.i.d. dropout must be compared
at matched *realised* rate, never at matched nominal rate. `realised_fn_rate` is
on every run record for exactly this reason. This is also a warning for the
terrain and pursuer dials: any dial whose intensity varies in space will have a
realised value that depends on where the swarm ends up.

Figures: `figures/occlusion_shakedown_curve.png`,
`figures/occlusion_shakedown_surface.png`.

---

## 2. Idea A, preliminary: terrain

`configs/sweeps/terrain_idea_a.toml` — n = 20, τ = 600 s, 100 runs/cell,
`g_eff` = 0.4, correlation length λ = 0.15 m = R₀.

Median final dispersion (flat clean arena = 1.40):

| slope | θ_m = 0 | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| 0° | 1.40 | 1.39 | 1.43 | 1.50 | 1.62 |
| 2.5° | 1.41 | 1.41 | 1.46 | 1.49 | 1.67 |
| 5° | 1.46 | 1.45 | 1.47 | 1.49 | 1.79 |
| 7.5° | 1.44 | 1.41 | 1.51 | 1.56 | 1.80 |
| 10° | 1.51 | 1.51 | 1.52 | 1.59 | 2.12 |
| 15° | 1.58 | 1.60 | 1.64 | 1.65 | **2841** |

### H1 is not supported by this sweep

H1 predicts that *small* α and θ_m help, as motion noise did in Daymude et al.
The trend here is monotone degradation on both dials. The only hint in H1's
direction is marginal — at θ_m = 0.1 the dispersion is a hair below the θ_m = 0
column at 0°, 5° and 7.5°, and the T = 0.7 contour on the surface figure bulges
slightly upward around α ≈ 2.5° — all well within run-to-run spread.

This is consistent with the actuation-noise result
(`docs/decisions/0004-baseline-actuation-noise.md`), where adding noise also
failed to help and mildly hurt. Two independent perturbations, same answer. The
"noise helps" intuition comes from a discrete model with a deterministic deadlock
to break; this continuous model does not appear to have one.

**Next:** test H1 properly with a fine sweep at small α (0–3°) and small θ_m
(0–0.1) at ≥ 100 runs/cell, rather than reading it off the corner of a coarse
grid. If it fails there too, H1 should be revised in the build doc rather than
quietly dropped.

### The (15°, θ_m = 0.5) cell is outside the model's usable range

Dispersion 2841 corresponds to the swarm spread over roughly 12 m. At that
corner `g_eff·sin α` = 0.104 m/s against a maximum wheel speed of 0.128 m/s, and
traction reaches 1.5, so robots are effectively rolling away downhill at
different rates. It is a real consequence of the model, not a numerical failure,
but it is a runaway regime rather than a degraded-aggregation one, and it should
be reported as the boundary of the dial range, not averaged into a trend.

### The dials are not interchangeable

At matched degradation the two dials behave differently: slope alone at 15°
reaches 1.58, while traction alone at θ_m = 0.5 reaches 1.62 — comparable — but
the single-cluster share falls to 0.54 under slope against 0.42 under traction.
Slope keeps the swarm together and drags it; traction breaks it up. That
distinction is what the two-dial surface is for, and it is the reason the build
doc's corrected model needs both mechanisms rather than one.

Figures: `figures/terrain_idea_a_surface.png`, `figures/terrain_idea_a_curve.png`.
