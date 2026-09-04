# Corrections to the build doc

Points where `docs/build-doc-v2.md` needs amending in light of sources checked
while building this repository. Each is a citation matter, not a design change;
the doc's structure and framing survive all of them.

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
