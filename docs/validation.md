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
| Small swarms aggregate, as Gauci et al. prove for n = 2 | **FAIL** at τ = 600 s — see below |
| Absolute dispersion values match the published curve | **not checked** — needs the paper |
| e-puck constants match Gauci et al. Table 1 | **not checked** — needs the paper |

Two of the open items need the paper in hand, and are flagged in the code at
`config::RobotConfig` and `metrics::dispersion`. Until they are closed, treat
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

### Hypothesis 1: angular aliasing of the sensor — **ruled out**

The state-1 constants (1.0, −1.0) spin the body at 2·v_max/ℓ = 4.83 rad/s, which
at dt = 0.1 s is 27.7° per control step. A body at 0.3 m subtends only 14.2°, so
a zero-width ray can step straight over its target — and the sparser the swarm,
the worse it gets, which matches the n-dependence exactly.

It is the wrong explanation. `configs/sweeps/timestep_fov_gate.toml`
(30 runs/cell, a diagnostic — do not quote as a result) gives median final
dispersion:

| n | dt | ray (fov 0) | fov 0.05 | fov 0.10 | fov 0.20 |
|---|---|---|---|---|---|
| 2 | 0.10 | 14.18 | 13.83 | 14.74 | 16.55 |
| 2 | 0.01 | **6.50** | 12.14 | 11.87 | 12.64 |
| 5 | 0.10 | 6.07 | 5.46 | 5.79 | 4.57 |
| 5 | 0.01 | 5.49 | 6.44 | 5.51 | 6.12 |
| 20 | 0.10 | 1.40 | 1.39 | 1.39 | 1.31 |
| 20 | 0.01 | 1.57 | 1.45 | 1.43 | 1.36 |

A ten-fold finer timestep moves n = 2 from 14.2 to 6.5 — better, but nowhere
near the ~1 that aggregation means. n = 5 does not move at all. And widening the
sensor's field of view makes n = 2 *worse*, which is the opposite of what an
aliasing story predicts: more time in the "seen" state means more time spinning
in place, and spinning is not approaching.

n = 20 is essentially unaffected by either dial, which is the reassuring part:
the regime the project actually works in is not sitting on a numerical cliff.

### Hypothesis 2: it is a time budget — **under test**

The mechanism explains the n-dependence without any numerical fault. A robot
that sees nothing traces a *closed circle*: constant wheel speeds, so it returns
to where it started and never translates. The only thing that relocates it is
rotating on the spot, which moves the centre of its next circle. Displacement
therefore accumulates one sighting at a time.

With n = 20 there is nearly always something in view. With n = 2 a robot can
circle for a long time before its ray crosses the other one, so the same
mechanism needs far more wall-clock. Gauci et al.'s n = 2 result is a proof, and
a proof is asymptotic; τ = 600 s is not.

`configs/sweeps/small_n_time_gate.toml` sweeps n ∈ {2,3,4,5,10} against
τ ∈ {600, 3000, 12000, 48000} s at 100 runs/cell to settle it. **If small n
aggregates given time, the gate closes and τ = 600 s is simply too short for
n < 10 — which then has to be stated wherever small swarms appear. If it does
not, there is a real discrepancy with the published result and it must be found
before anything downstream is trusted.**

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
