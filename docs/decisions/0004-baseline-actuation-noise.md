# 0004 — Actuation noise is a dial, and it is off by default

**Status:** accepted, 2026-09-04.

## Context

Chasing the week-1 gate failure at small `n` (see `docs/validation.md`), one
hypothesis was that the simulator was missing baseline motion noise. The
reasoning was sound: with constant wheel speeds the state-0 trajectory is an
*exactly closed* circle, so a robot that sees nothing returns to where it
started and never explores. Real e-pucks slip. Daymude et al. (2021) report that
collisions and slipping are what break deterministic deadlock in practice, and
the build doc's H1 leans on the same observation — "small α and θ_m help, as
motion noise did in Daymude et al."

## Decision

Add per-wheel Gaussian actuation noise as `noise.wheel_noise`, expressed as a
fraction of `max_wheel_speed`, and **default it to zero**.

## Why zero

It was measured, and it does not do what the hypothesis predicted
(50 runs/cell, median final dispersion):

| `wheel_noise` | n = 2 | n = 5 | n = 20 | n = 20, share single cluster |
|---|---|---|---|---|
| 0.00 | 14.18 | 5.43 | 1.37 | 0.94 |
| 0.01 | 11.23 | 5.94 | 1.41 | 0.84 |
| 0.05 | 16.95 | 6.15 | 1.42 | 0.70 |
| 0.20 | 10.48 | 6.40 | 1.44 | 0.66 |

Small `n` is unaffected — the failure is not an exploration problem — and at
n = 20 noise is mildly *harmful*, taking the share of runs ending as a single
cluster from 0.94 to 0.66.

That is worth stating plainly, because it does not match the expectation carried
over from Daymude et al.: their result is about a *discrete* model where noise
breaks a deterministic deadlock, and this continuous model does not have that
deadlock to break. H1 should be tested on its own terms rather than assumed.

Defaulting to zero keeps the reference baseline the noise-free idealisation that
Gauci's simulation uses. Turning noise on silently would have shifted every
number measured against that baseline, in the direction that flatters nothing.

## Consequences

* `noise.wheel_noise` is a dial to sweep, not a correction to apply.
* It is distinct from `terrain.slip_noise`, which scales with `|sin α|` and is
  therefore zero on a flat board. Slope-induced slip is part of the terrain
  model; this is a property of the robot.
* H1 ("small α and θ_m help") remains open and is now more interesting: if
  actuation noise does not help here, the Idea A prediction that *terrain* noise
  helps needs its own evidence rather than an argument by analogy.
