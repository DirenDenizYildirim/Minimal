# Validation

What has actually been checked, and what has not. The build doc puts a **gate**
at the end of week 1: reproduce Gauci's constants and scaling curve before adding
a single hostility dial. This file is that gate's record.

Everything below was measured on this simulator at the commit that introduced
it. Re-run with the config named in each section; all results are seeded and
reproduce bit-for-bit.

---

## Gate status: **NOT PASSED**

| Check | Status |
|---|---|
| The published constants aggregate a swarm in a clean arena | **pass** (n ≥ 10) |
| Dispersion of a packed cluster is O(1) under our normalisation | **pass** |
| Aggregation improves monotonically with swarm size | **pass** (n = 10 → 100) |
| Small swarms aggregate, as Gauci et al. prove for n = 2 | **FAIL** with a zero-width sensor ray; recovered by a wide sensor cone — see §2 |
| The sensor's field of view matches Gauci's | **not checked** — needs the paper; it is what the n = 2 result hinges on |
| Absolute dispersion values match the published curve | **not checked** — needs the paper |
| e-puck constants match Gauci et al. Table 1 | **not checked** — needs the paper |

Three of the open items need the paper in hand, and are flagged in the code at
`config::RobotConfig`, `sensor::SensorConfig::fov_half_angle` and `metrics::dispersion`. Until they are closed, treat
every **absolute** number from this simulator as provisional. Comparisons
*between* cells — which is what the whole project is — are unaffected, because
they share the normalisation.

---

## 1. Aggregation in a clean arena

`configs/sweeps/gauci_scaling.toml` — 100 runs/cell, n = 20 default arena,
τ = 600 s, dt = 0.1 s.

| n | dispersion at t = 0 | dispersion at τ | ratio | share of time single cluster |
|---|---|---|---|---|
| 2 | 8.09 | **12.98** | **1.60** | 0.08 |
| 5 | 16.93 | **5.56** | 0.33 | 0.03 |
| 10 | 18.57 | 1.81 | 0.098 | 0.57 |
| 20 | 19.22 | 1.40 | 0.073 | 0.77 |
| 50 | 19.20 | 1.20 | 0.063 | 0.89 |
| 100 | 19.84 | 1.15 | 0.058 | 0.90 |

For n ≥ 10 this is what aggregation looks like: the swarm contracts by more than
an order of magnitude and lands close to the packed-cluster value of ~1, getting
closer as n grows (a larger cluster is better approximated by the uniform disk
the normaliser assumes).

For n = 2 and n = 5 it does not aggregate. n = 2 ends *further apart* than it
started (0.21 m → 0.27 m centre to centre).

## 2. Diagnosing the small-n failure

Four hypotheses, three ruled out by measurement. The surviving one identifies a
modelling parameter that has to be read off the paper.

### H-A: angular aliasing of the sensor — **ruled out**

The state-1 constants (1.0, −1.0) spin the body at 2·v_max/ℓ = 4.83 rad/s, which
at dt = 0.1 s is 27.7° per control step. A body at 0.3 m subtends only 14.2°, so
a zero-width ray can step straight over its target — and the sparser the swarm
the worse it gets, which matches the n-dependence exactly.

`configs/sweeps/timestep_fov_gate.toml` (30 runs/cell — a diagnostic, not a
result). Median final dispersion:

| n | dt | ray (fov 0) | fov 0.05 | fov 0.10 | fov 0.20 |
|---|---|---|---|---|---|
| 2 | 0.10 | 14.18 | 13.83 | 14.74 | 16.55 |
| 2 | 0.01 | **6.50** | 12.14 | 11.87 | 12.64 |
| 5 | 0.10 | 6.07 | 5.46 | 5.79 | 4.57 |
| 5 | 0.01 | 5.49 | 6.44 | 5.51 | 6.12 |
| 20 | 0.10 | 1.40 | 1.39 | 1.39 | 1.31 |
| 20 | 0.01 | 1.57 | 1.45 | 1.43 | 1.36 |

A ten-fold finer timestep moves n = 2 from 14.2 to 6.5 — better, nowhere near
the ~1 that aggregation means. n = 5 does not move. n = 20 is essentially
unaffected by either dial, which is the reassuring part: the regime the project
works in is not sitting on a numerical cliff.

### H-B: it is a time budget — **ruled out**

A robot that sees nothing traces a *closed* circle and never translates; only
rotating on the spot relocates the centre of its next circle. Displacement
accumulates one sighting at a time, and with n = 2 sightings are rare. A proof
is asymptotic; τ = 600 s is not.

`configs/sweeps/small_n_time_gate.toml`, 100 runs/cell. Median final dispersion:

| n | τ = 600 | τ = 3 000 | τ = 12 000 | τ = 48 000 |
|---|---|---|---|---|
| 2 | 12.98 | 6.95 | 19.07 | 6.53 |
| 3 | 12.13 | 11.29 | 12.55 | 11.48 |
| 4 | 8.30 | 8.94 | 9.12 | 8.82 |
| 5 | 5.56 | 5.97 | 6.44 | 6.59 |
| 10 | 1.81 | 1.87 | 1.93 | 1.87 |

Flat in τ across eighty-fold. Small swarms are not slow to aggregate; they do
not aggregate.

### H-C: missing baseline actuation noise — **ruled out**

Recorded in full in `docs/decisions/0004-baseline-actuation-noise.md`. Adding
per-wheel Gaussian noise leaves small n where it was and mildly *hurts* n = 20
(share of runs ending as a single cluster falls from 0.94 to 0.66 at 5% noise).
The dial is kept, defaulted to zero, and H1 is now an open question rather than
an assumption carried over from Daymude et al.

Initial separation was checked at the same time and is also not the cause: at
n = 2, starting the pair anywhere from 0.05 m (in contact) to 1.2 m (8·R₀) gives
final dispersion 12.6–16.4 and a single cluster in under 7% of runs. Started
touching, they separate.

### H-D: the sensor cone is too narrow — **supported, and the open item**

Sweeping the sensor's half-FOV far wider than the first diagnostic did, at
60 runs/cell (median final dispersion / share of runs ending as a single cluster):

| half-FOV | n = 2 | n = 5 | n = 20 |
|---|---|---|---|
| 0.0° (bare ray) | 16.85 / 0.03 | 6.06 / 0.02 | 1.41 / 0.73 |
| 5.7° | 17.85 / 0.03 | 5.94 / 0.08 | 1.37 / 0.92 |
| 17.2° | 18.72 / 0.02 | 5.29 / 0.05 | 1.30 / 0.98 |
| 28.6° | 18.40 / 0.00 | 4.02 / 0.22 | 1.26 / 1.00 |
| 45.8° | 17.81 / 0.00 | 2.69 / 0.55 | 1.19 / 1.00 |
| 68.8° | 15.95 / 0.00 | **1.13 / 1.00** | 1.17 / 1.00 |
| 90.0° | **1.00 / 1.00** | 1.13 / 1.00 | 1.21 / 1.00 |

Monotone, and it closes the gap completely: n = 5 aggregates fully from 68.8°,
and n = 2 reaches exact contact (dispersion 1.00, every run) at 90°.

The mechanism this implies is coherent with the controller. State-0 wheel speeds
are both **negative**, so a robot that sees nothing drives *backwards* along its
heading, while the sensor faces forwards. A wide cone makes "I see nothing" a
reliable statement that the other robot is *behind* me — and backward motion
then closes the distance. With a bare ray, "I see nothing" carries almost no
information about where the other robot is, and the approach mechanism is gone.
Density substitutes for it: at n = 20 something is nearly always in view, which
is why the ray model aggregates there and nowhere else.

### What this means for the gate

`sensor.fov_half_angle` is a **physical parameter of Gauci's setup that we have
guessed**, and the guess (a zero-width ray) is very likely wrong. It cannot be
chosen by picking whichever value reproduces the published result — that is
fitting the model to the answer. It has to be read off the paper's sensor
specification and then checked against the n = 2 result.

Until then the gate stays open, and results at n ≥ 10 — which is every sweep in
this repository — are qualitatively insensitive to it (dispersion 1.41 → 1.17
across the full range). Small-swarm results must not be quoted at all.

## 3. Metric sensitivity

`configs/sweeps/link_distance_sensitivity.toml` — 30 runs/cell.

| link distance | single cluster at τ | share of time single | final dispersion |
|---|---|---|---|
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
