# Corrections to the build doc

Points where `docs/build-doc-v2.md` needs amending — some from sources checked
while building this repository, some from results it produced.

**The three that change the plan rather than a citation:**

1. **Handling time is required** (§7). Idea B's pursuer does not work without it;
   with capture free on contact, a cluster is a buffet and aggregation is
   maximally bad under any metric.
2. **The scalar-field mechanism claim is confirmed** (§9). The build doc's
   correction to Idea A was necessary, and there is now a paired control saying
   so rather than an argument.
3. **The Steinberg & Solovey impossibility result is the framing anchor** (§2).
   It belongs in the framing section, not the reading list: `c*(θ)` is a function
   of swarm size as well as environment, and part of the answer to "minimality is
   ill-defined" is now a theorem.

## 1. The Gauci n = 2 proof has been disproven

**Build doc §1.1** describes the Gauci row as "Exhaustive grid search at 4
constants; **proof for n = 2**; empirical to 1000."

Steinberg and Solovey (2024), *Impossibility of Self-Organized Aggregation
without Computation* (arXiv:2501.00390; IEEE 2025) identify an unsound implicit
assumption in that proof — that a distance condition `d ≤ 2(R+r)` guarantees
subsequent aggregation, when two robots can satisfy it while travelling the same
circular perimeter without ever seeing each other. They report the Gauci
controller failing to aggregate on **4.24%** of two-robot trials, and give an
alternative controller, `u* = (−a, a, b, b)` with `a, b ∈ (0,1]`, with a correct
proof.

Suggested amendment: "Exhaustive grid search at 4 constants; empirical to 1000.
The published n = 2 proof is unsound (Steinberg & Solovey 2024), who give a
corrected controller and proof."

## 2. There is an impossibility result for the whole capability class

Not in the build doc at all, and it deserves to be in §2, not the reading list.

Steinberg and Solovey prove: for any bimodal controller in this class —
memoryless, binary line-of-sight sensor, no communication — there exists a swarm
size `n` and an initial state for which it does not aggregate. Assumptions:
plastic collisions, no noise, no slippage.

This sharpens §2.2 rather than undermining it. The doc already insists that
optimiser-found minima are upper bounds; this says that for one whole capability
row the minimum does not exist uniformly in `n` at all. `c*(θ)` is therefore a
function of the swarm size as well as the environment, and the papers should say
so. It is also a direct answer to the "minimality is ill-defined" objection in
§7: part of the answer is now a theorem.

## 3. Daymude et al.'s deadlock threshold: n > 3

**Build doc §1.1** says "Deadlock exists for n > 3 under deterministic uniform
motion (**verify exact n before quoting**)".

Verified: "there exist deadlocked configurations from which this algorithm
cannot achieve aggregation for **n > 3** robots when the robots' motion is
uniform and deterministic." The doc's figure is correct as written; the
parenthetical can be dropped.

Their practical caveat is also worth quoting exactly, because H1 leans on it:
the deadlocks "are not observed in practice due to inherent noise in physical
e-puck robots — collisions and slipping perturb the precise balancing of forces
to allow robots to push past one another."

Note that this repository's actuation-noise probe found no such benefit in a
continuous model (`docs/decisions/0004-baseline-actuation-noise.md`), which is
consistent: the mechanism they describe is about breaking a *force balance* in
contact, not about exploration.

## 4. Simulation parameters worth stating in the methods section

From the Gauci et al. setup, all verified and now pinned by a test:

* Enki, e-puck modelled as a disk of diameter 7.4 cm, mass 152 g, inter-wheel
  distance **5.1 cm**, wheel velocities in ±12.8 cm/s.
* Control cycle **0.1 s**, physics updated **10× per control cycle**.
* Line-of-sight sensor: a **ray** cast from the e-puck's front, returning the
  first body it intersects. Infinite range. The paper separately proves a
  sufficiently long range is necessary.
* Derived: turn radius **14.45 cm**, ω₀ = **−0.75 rad/s**, ω₁ = **−5.02 rad/s**.

## Reading-list additions

* Steinberg, R. & Solovey, K. (2024/2025). *Impossibility of Self-Organized
  Aggregation without Computation*. arXiv:2501.00390.

## 5. H1 should be withdrawn, or narrowed to a mechanism this model does not have

**Build doc, Idea A, H1:** "small α and θ_m help, as motion noise did in Daymude
et al."

Three independent tests, all null:

| test | design | result |
|---|---|---|
| Actuation noise | per-wheel Gaussian noise, 0–20% of max wheel speed, 50 runs/cell | no benefit at any n; n = 20 mildly harmed |
| Coarse terrain grid | α to 15°, θ_m to 0.5, 100 runs/cell | monotone degradation on both dials |
| Fine H1 sweep | α ≤ 3°, θ_m ≤ 0.1, **200 runs/cell** | 0 of 23 cells has a CI disjoint from baseline; whole grid within 1.385–1.430 |

The last of those was designed specifically to give H1 its best chance — a dense
neighbourhood of zero, double the usual runs — and found nothing.

The likely reason is that the analogy imports a conclusion without its mechanism.
Daymude et al. are precise about theirs: noise "perturbs the precise balancing of
forces to allow robots to push past one another". That is a statement about
breaking a **contact deadlock**, in a discrete model where such deadlocks are
proven to exist for n > 3. It is not a claim that perturbation aids exploration
or mixing in general. This continuous model has no proven deadlock, and both the
noise probe and the terrain sweeps behave as if it has none to break.

**Suggested amendment.** Replace H1 with either:

* *(withdrawn)* — drop the prediction, and note that terrain degrades
  monotonically on both dials, with the interesting structure in *which* dial
  and *at what length scale* (H2) rather than in a non-monotonicity; or
* *(narrowed)* — "if the continuous model exhibits Daymude-style contact
  deadlocks, small α and θ_m should relieve them" — which is a testable
  prediction, but requires first showing the deadlocks exist here. Nothing in
  this repository suggests they do at n = 20.

Either way it should not survive into Paper 1 as written. A hypothesis that has
failed three times and whose mechanism does not transfer is not a hypothesis the
paper should be defending.

## 6. Idea A's threshold belongs on dispersion, not on a cluster count

Related, and a measurement point rather than a citation one. Across the whole
Idea A terrain grid the share of runs that *ever* reach a single cluster is 1.00
in every cell except the runaway corner. Terrain at n = 20 does not stop the
swarm aggregating; it makes the cluster looser and harder to hold.

So a threshold `T` set on "did they aggregate" would see almost nothing, while
one set on dispersion sees a clean monotone signal. The build doc lists
dispersion first among Idea A's metrics already — this is a reason to make that
binding rather than a preference.

## 7. Handling time is required, not optional

Not in the build doc, and Idea B does not work without it.

The doc corrected v1's pursuer by giving it perception limits — finite range and
confusion — so that aggregation *could* protect a swarm. But capture remained
free: instantaneous on contact. With zero handling time a packed cluster is a
buffet, the pursuer takes one robot per control step, and twenty robots are gone
in two seconds. Aggregation is then maximally bad under any metric, which is the
v1 failure mode reappearing one level down.

Handling time — Holling's, the interval after a capture during which the predator
is occupied — is what makes dilution exist at all. Measured here: with handling
comparable to the pursuer's travel time between neighbours the aggregating rows
multiply survival ×3.05 as confusion rises; at 5× that travel time the same
figure is ×4.10, while a dispersive control with identical sensing gains ×1.13.

Suggested amendment to Idea B's pursuer family: add `h`, the handling time, as a
fourth pursuer dial alongside ρ, r_p and κ, and set it relative to the pursuer's
travel time between neighbouring robots in a formed cluster.

## 8. A dispersive control row belongs in Idea B's design

The build doc's rows B0–B4 all aggregate when no pursuer is in view, so none of
them can distinguish "the swarm aggregated" from "the pursuer's perception is
poor". Adding one row with identical pursuer sensing and no clustering settles
it in a single sweep (`docs/findings.md` §8), and without it the headline
question — does aggregation protect the swarm? — is not answerable by that grid.

The answer it gives is also worth carrying into the framing: confusion helps
aggregating rows 2–4× and a dispersive row 1.1×, so the dilution mechanism is
real; but over the swept grid the dispersive row still survives better on
average. Aggregation stops being catastrophic; it does not become the better bet.

## 9. The corrected terrain model is necessary, and there is now a control for it

**Build doc, Idea A, "What was wrong in v1".** The doc argues that a scalar speed
field cannot deform one robot's path relative to another's, and replaces it with
the per-wheel model. The argument is correct but it was never tested — and
"cannot deform a trajectory" is not the same claim as "cannot break aggregation",
since a scalar field still makes robots in different places move at different
rates.

Tested as a paired comparison, identical seeds and field, differing only in how
the field is sampled (`docs/findings.md` §6). Pooled over every θ_m > 0 cell,
1800 runs each:

* per-wheel **1.175 [1.154, 1.190]**
* scalar-centre **0.980 [0.976, 0.986]**

The scalar field produces no degradation anywhere on the grid — no peak, flat
within [0.96, 1.01]. So the v1 model would have measured nothing, and the paper
can support the correction with a control rather than with reasoning.

Suggested amendment: keep the argument, and add the measurement. It converts a
methodological aside into a result, and it is cheap to state.

## 10. Report θ_m only up to 1/max|f|

Housekeeping, but it changes a published figure. The traction field reaches
|f| = 1, so at θ_m = 1 the multiplier `1 + θ_m·f` can reach zero, a wheel stalls
and the robot pivots. Any sweep above that is measuring stall, not terrain.
Sweeps here are cut at θ_m = 0.9 and figures at 1.0.
