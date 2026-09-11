# Validation

What has actually been checked, and what has not. The build doc puts a **gate**
at the end of week 1: reproduce Gauci's constants and scaling curve before adding
a single hostility dial. This file is that gate's record.

Everything below was measured on this simulator at the commit that introduced
it. Re-run with the config named in each section; all results are seeded and
reproduce bit-for-bit.

---

## Gate status: **PASSED**, with the small-n criterion corrected

| Check | Status |
|---|---|
| e-puck constants match Gauci et al. | **pass, and one was wrong** — inter-wheel distance is 5.1 cm, not the 5.3 cm assumed. Fixed. |
| The published derived quantities reproduce (R₀ = 14.45 cm, ω₀ = 0.75, ω₁ = 5.02 rad/s) | **pass**, to 5e-5 m and 5e-3 rad/s, and pinned by a test |
| The sensor model matches Gauci's | **pass** — a zero-width ray from the robot's front, which is what was implemented |
| The control cycle matches (0.1 s) | **pass** — and shown irrelevant over a 50-fold range |
| The published constants aggregate a swarm in a clean arena | **pass** (n ≥ 10) |
| Dispersion of a packed cluster is O(1) under our normalisation | **pass** |
| Aggregation improves monotonically with swarm size | **pass** (n = 10 → 100) |
| Small swarms aggregate | **pass, against the corrected criterion** — 87–93% of pairs reach connectivity, against the ~95.8% reported for this controller in the literature |
| Absolute dispersion values match the published curve | **not checked** — needs the paper's figures |

### How the small-n row resolved

It failed for two weeks' worth of reasons that were all wrong, and then turned
out to be a fault in the check rather than the simulator.

The check appealed to Gauci et al.'s Theorem 3, "two robots always aggregate".
**That proof has since been disproven** — Steinberg and Solovey (2024) identify
an unsound implicit assumption in it and report the same controller failing on
4.24% of two-robot trials. And the literature's definition of aggregation is
*reaching* a connected configuration, not being in one at τ, which for a pair is
a difference of an order of magnitude: 93% of pairs here reach exact contact and
only ~10% are still touching at τ.

Measured against the criterion the literature actually uses, this simulator
agrees with it. Full reasoning in
`docs/decisions/0005-aggregation-criterion.md`; the consequences for the build
doc's citations are in `docs/literature-corrections.md`.

The five hypotheses tested before that are kept in §2 — they are real
sensitivity measurements, and three of them are useful results in their own right.

### Sources for the verified rows

* Enki robot model: "the body of an e-puck is modeled as a disk of diameter
  7.4 cm and mass 152 g, with an inter-wheel distance of **5.1 cm**, and the
  velocities of the left and right wheels can be set independently in
  [−12.8, 12.8] cm/s."
* Sensor: "the binary sensor was realized by projecting a line from the robot's
  front and checking whether it intersects with another robot's body … the
  line-of-sight sensor in Enki is simulated by **casting a ray** from the
  e-puck's front and checking the first item with which it intersects." Range is
  infinite; the paper separately proves that a sufficiently long range is
  necessary.
* Controller: x* = (−0.7, −1, 1, −1); "when no robot is seen, a robot will rotate
  around a point 90° counter-clockwise from its line-of-sight sensor and
  **14.45 cm** away at a speed of **ω₀ = −0.75 rad/s**; when a robot is seen, it
  will rotate clockwise in place at a speed of **ω₁ = −5.02 rad/s**." The n = 2
  case is *proven* to aggregate in finite time.

`controller::tests::published_derived_quantities_reproduce` ties the wheel
constants, the body geometry and the kinematics together against those three
numbers. It is the strongest single check in the gate, and it is what caught the
inter-wheel distance.

The one remaining unverified row needs the paper's figures, and is flagged in
the code at `metrics::dispersion`: our normalisation is derived so that a packed
cluster scores ~1, and the baseline lands at 1.40, but the exact constant Gauci
reports has not been checked. Until it is, treat **absolute** dispersion values
as provisional. Comparisons *between* cells — which is what the whole project is
— are unaffected, because they share the normalisation.

---

## 1. Aggregation in a clean arena

`configs/sweeps/gauci_scaling.toml` — 100 runs/cell, τ = 600 s, dt = 0.1 s, at
the corrected inter-wheel distance. The simulator reports R₀ = **14.45 cm**,
matching the published figure exactly.

| n | dispersion at t = 0 | dispersion at τ | ratio | **ever one cluster** | one cluster at τ | share of time |
|---|---|---|---|---|---|---|
| 2 | 8.09 | 8.84 | 1.09 | **0.88** | 0.15 | 0.10 |
| 5 | 16.93 | 5.30 | 0.31 | **0.98** | 0.09 | 0.05 |
| 10 | 18.57 | 1.68 | 0.090 | **1.00** | 0.72 | 0.67 |
| 20 | 19.22 | 1.43 | 0.074 | **1.00** | 0.78 | 0.80 |
| 50 | 19.20 | 1.20 | 0.063 | **1.00** | 0.93 | 0.87 |
| 100 | 19.84 | 1.15 | 0.058 | **1.00** | 0.97 | 0.90 |

Read the **ever** column: that is the criterion the literature uses (ADR 0005).
Every swarm of ten or more aggregates in every run, and small swarms aggregate in
88–98% of runs, against the ~95.8% reported for this controller at n = 2.

Read the dispersion column for how *tightly*: an order of magnitude of
contraction at n ≥ 10, approaching the packed-cluster value of ~1 as n grows,
which is expected — a larger cluster is better approximated by the uniform disk
the normaliser assumes.

The two small-n columns diverge because nothing in the controller holds a pair
together once it arrives. At contact the other robot subtends about 60°, so a
robot is frozen for a sixth of each rotation and backing away for the rest; a
dense cluster subtends far more, robots are frozen most of the time, and they
accumulate. Same controller, opposite outcome, and the reason is angular size.

## 2. Diagnosing the small-n failure

Five hypotheses, all wrong. Kept because three of them are useful sensitivity
results in their own right, and because the sequence is a fair record of how the
real cause was found — which was not by instrumenting the simulator.

All five were re-run at the corrected inter-wheel distance, and all are reported
below with the aggregation criterion the gate settled on (`ever_single_cluster`)
alongside dispersion, since that is what changed the verdict.

### H-A: angular aliasing of the sensor — **ruled out**

The state-1 constants spin the body at ω₁ = 5.02 rad/s, which at dt = 0.1 s is
28.8° per control step, while a body at 20 cm subtends only 21°. A zero-width ray
can step over its target — and the sparser the swarm, the worse it gets.

`configs/sweeps/timestep_fov_gate.toml`, median final dispersion:

| n | dt | ray | fov 0.05 | fov 0.10 | fov 0.20 |
|---|---|---|---|---|---|
| 2 | 0.10 | 5.83 | 7.02 | 5.97 | 6.36 |
| 2 | 0.01 | 8.02 | 5.28 | 6.05 | 6.46 |
| 5 | 0.10 | 5.28 | 5.81 | 5.02 | 4.88 |
| 20 | 0.10 | 1.39 | 1.40 | 1.37 | 1.34 |
| 20 | 0.01 | 1.42 | 1.40 | 1.41 | 1.33 |

No trend in either dial. n = 20 is unaffected throughout, which is the
reassuring part: the regime the project works in is not on a numerical cliff.

### H-B: it is a time budget — **ruled out**

`configs/sweeps/small_n_time_gate.toml`, 100 runs/cell. Median final dispersion
/ share ever forming a single cluster:

| n | τ = 600 | τ = 3 000 | τ = 12 000 | τ = 48 000 |
|---|---|---|---|---|
| 2 | 8.84 / 0.88 | 24.99 / 0.89 | 6.57 / 0.89 | 7.13 / 0.89 |
| 3 | 10.96 / 0.25 | 14.01 / 0.29 | 9.95 / 0.29 | 10.16 / 0.29 |
| 4 | 7.89 / 0.53 | 7.90 / 0.56 | 8.42 / 0.56 | 8.14 / 0.56 |
| 5 | 5.30 / 0.98 | 5.00 / 1.00 | 5.83 / 1.00 | 6.25 / 1.00 |
| 10 | 1.68 / 1.00 | 1.68 / 1.00 | 1.71 / 1.00 | 1.67 / 1.00 |

Flat in τ across eighty-fold: whatever a swarm is going to do, it has done by
600 s.

**An open observation.** n = 3 and n = 4 reach a single cluster far less often
than either n = 2 or n = 5, and the dip does not close with time. The tempting
reading is Daymude et al.'s deadlock, which they prove for n > 3 under uniform
deterministic motion. But the simpler explanation is combinatorial: "all robots
in one connected component" is a harder event for three or four robots than for
two, and easier again once density rises. Distinguishing the two would need the
deadlock configurations checked directly, and nothing downstream depends on it.
Recorded, not claimed.

### H-C: missing baseline actuation noise — **ruled out**

`configs/sweeps/small_n_noise_probe.toml`. Median final dispersion:

| `wheel_noise` | n = 2 | n = 5 | n = 20 |
|---|---|---|---|
| 0.00 | 6.40 | 5.36 | 1.41 |
| 0.02 | 11.61 | 5.22 | 1.40 |
| 0.05 | 12.01 | 4.64 | 1.39 |
| 0.20 | 10.92 | 5.55 | 1.45 |

No benefit anywhere, and n = 20 reaches a single cluster in every run at every
noise level. Recorded in full in
`docs/decisions/0004-baseline-actuation-noise.md`.

Initial separation was checked alongside
(`configs/sweeps/small_n_start_radius_probe.toml`) and is also not the cause: at
n = 2 the pair reaches a single cluster in 86–100% of runs at every start radius
from 0.05 m (in contact) to 1.2 m (8·R₀), while final dispersion stays at 8–12
throughout. They find each other and then drift apart, wherever they begin.

### H-D: the sensor cone is too narrow — **refuted by the source**

This one looked strong and was wrong twice over.

`configs/sweeps/sensor_fov_gate.toml`, median final dispersion / share ever
forming a single cluster:

| half-FOV | n = 2 | n = 5 | n = 20 |
|---|---|---|---|
| 0.0° (bare ray) | 8.28 / 0.90 | 5.41 / 0.97 | 1.41 / 1.00 |
| 17.2° | 8.36 / 0.72 | 4.57 / 1.00 | 1.31 / 1.00 |
| 28.6° | 11.06 / 0.45 | 4.10 / 1.00 | 1.25 / 1.00 |
| 45.8° | 15.64 / 0.17 | 2.89 / 1.00 | 1.19 / 1.00 |
| 68.8° | 14.19 / 0.18 | 1.14 / 1.00 | 1.16 / 1.00 |
| 90.0° | 1.00 / 1.00 | 1.13 / 1.00 | 1.21 / 1.00 |

Wrong for the first reason: **it is not what Gauci did.** The paper casts a ray
from the e-puck's front and takes the first body it intersects — a zero-width
ray, exactly what was already implemented. This table measures a *deviation from*
the published model, not a correction toward it.

Wrong for the second reason: under the aggregation criterion the gate eventually
settled on, widening the cone makes n = 2 **worse**, not better — the share of
pairs that ever reach a single cluster falls from 0.90 to 0.17 before the
degenerate 90° case, where both robots simply freeze on sight and never move.
The apparent "recovery" was an artefact of scoring dispersion at τ.

Kept as a committed sweep because it is a genuine sensitivity result: at n ≥ 10
the field of view barely matters, which is worth knowing for the hardware track,
where a real camera is not a ray.

### H-E: discretisation of the sensor reading — **ruled out**

`configs/sweeps/timestep_convergence.toml`, 100 runs/cell, median final
dispersion at n = 2:

| dt | °/step | τ = 600 | τ = 6000 |
|---|---|---|---|
| 0.002 | 0.6 | 14.32 | 12.58 |
| 0.010 | 2.9 | 12.92 | 9.34 |
| 0.050 | 14.4 | 12.47 | 6.20 |
| 0.100 | 28.8 | 8.84 | 6.16 |

Fifty-fold refinement changes nothing, and if anything the coarse step does
better. Independently, the paper states its control cycle **was** 0.1 s with
physics updated ten times per cycle — and since integration here is exact-arc,
substepping a constant-wheel-speed arc is a no-op. The timestep is neither wrong
nor load-bearing.

### H-F: the criterion was wrong — **this was it**

See the gate status above and `docs/decisions/0005-aggregation-criterion.md`.

### What the five wrong hypotheses were worth

Three of them are useful measurements regardless: the field-of-view sensitivity
matters for the hardware track, where a real camera is not a ray; the timestep
convergence bounds the integration error; and the actuation-noise probe produced
a finding that contradicts an assumption the build doc's H1 rests on.

The methodological lesson is cheaper to state than it was to learn: **when a
reproduction fails, check the claim before checking the code.** Four rounds of
instrumentation went into a discrepancy whose cause was a disproven theorem and
a mis-specified metric.

## 3. Metric sensitivity

`configs/sweeps/link_distance_sensitivity.toml` — 30 runs/cell.

| link distance | single cluster at τ | share of time single | final dispersion |
|---|---|---|---|
> **Freeze lift 1, finding F1: this whole table was produced at
> `axle_length = 0.053` and returns cell for cell at that value.** The committed
> baseline is 0.051 (§13 row 2, corrected from 5.3 cm as a literature error), and
> at 0.051 the dispersion column reads **1.3875 at every link distance** — spread
> still exactly zero — and the single-cluster share runs **0.475 → 0.967**. §13
> rows 13 and 14 carry the corrected values; this table is kept as it was
> measured, because it is what shows the cause. See `verification-report.md`.
> **Nothing the table is cited for changes**: the invariance of dispersion to the
> link distance is exact at both axle lengths, which is the whole point of it.

| 2.2 R | 0.73 | 0.43 | 1.401 |
| 2.5 R | 0.87 | 0.62 | 1.401 |
| 3.0 R | 0.90 | 0.77 | 1.401 |
| 3.5 R | 0.97 | 0.86 | 1.401 |
| 4.0 R | 1.00 | 0.92 | 1.401 |
| 5.0 R | 1.00 | 0.97 | 1.401 |
| 6.0 R | 1.00 | 0.98 | 1.401 |

Dispersion does not move at all; the cluster metrics move a lot. This is why
dispersion carries the threshold and cluster counts are secondary — see
`docs/decisions/0003-metrics.md`.

## 4. Contact resolution

Positional relaxation with early exit at a residual-overlap tolerance. Measured
on 25 robots after 600 steps, worst residual overlap as a share of body diameter:

| max passes | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|
| worst overlap | 5.0% | 1.3% | 0.05% | 0.01% | 0.01% |

Converged by 32 passes, which is the default. The early exit means a sparse
swarm pays for one pass. `world::tests::contact_resolution_keeps_residual_overlap_negligible`
holds the line at 0.1%.

## 5. Throughput

Release build, 4 cores: ~0.25 s per trial at n = 20, τ = 600 s, dt = 0.1 s;
the O(n²) sensor loop dominates. 4000 trials of the occlusion shakedown took
about four minutes. The build doc's 10⁵–10⁶ run budget at n = 50 is roughly
2–20 core-hours per full sweep, which is a cluster job, not a laptop job.

---

## What the invariants are, and where they live

These are checked by `cargo test` on every commit, so they cannot silently
regress:

* **Exact-arc integration.** One period of the state-0 constants closes to
  within 1e-9 m and holds radius `R0` throughout; the result is independent of
  the timestep. (`robot.rs`)
* **`R0` is the controller's only intrinsic length scale.** Scaling both wheels
  equally leaves the turn radius invariant — the reason v1's scalar speed field
  could not break symmetry. Per-wheel scaling does change it. (`terrain.rs`)
* **Terrain deforms the trajectory, not just its position.** With the linear
  drift removed, a slope stretches the state-0 loop along the fall line
  (+4.6% at 10°, growing with α), and a traction field alone deforms it. Flat
  terrain leaves a circle to within 1e-6. A Galilean drift could do none of this.
  (`terrain.rs`)
* **The sensor is a real line of sight.** Bodies ahead are seen, bodies behind
  are not, a body just off-axis by more than its angular half-width is missed,
  and a nearer body occludes a further one. (`sensor.rs`)
* **Dispersion is translation- and rotation-invariant** and scores a packed
  hexagonal lattice at O(1). (`metrics.rs`)
* **Runs are bit-for-bit reproducible** from `(seed, run_index)`, and the
  environment fields draw from separate seed streams so changing `n` does not
  reshuffle the terrain. (`world.rs`, `rng.rs`)
* **Time-resolved aggregates do not depend on the series being stored**, so a
  sweep can drop it for file size. (`world.rs`)
* **Only enumerated rows report a tight minimum**, and an unlabelled row
  defaults to the pessimistic assumption. (`controller.rs`)
