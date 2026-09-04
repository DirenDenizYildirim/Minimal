# Corrections to the build doc

Points where `docs/build-doc-v2.md` needs amending — some from sources checked
while building this repository, some from results it produced. The doc's
structure and framing survive all of them; §5 is the only one that changes a
prediction rather than a citation.

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
