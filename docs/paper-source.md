# Paper source — Minimal Swarms in Hostile Environments (Paper 1)

Everything needed to write the journal paper, in one file. Nothing here requires
opening `docs/findings.md`, `docs/literature-corrections.md`, a figure script, a
config, or the code. Where a number appears it is quoted at the precision the
source recorded it, with its interval, run count and provenance.

Compiled at the freeze commit **`ce427a8` (experimental record) / `2b736de` (freeze declaration)**. The evidence base is
`docs/findings.md` §1–§21 and `docs/literature-corrections.md` #1–#15; no
simulation was run after that commit for this paper.

Conventions used throughout this file:

* **†** — searched by an optimiser, not exhaustive. Any minimum read off such a
  row is an **upper bound**: "no controller found meeting T" means *not found*,
  not *not possible*.
* **‡** — hand-designed, not searched. Not even an upper bound in the sense †
  rows are: it says one guess did not work, and is evidence about that
  arrangement, not about the capability.
* Unmarked — enumerated at the source's resolution, and therefore **tight**.
  Only Gauci's four constants and rows built directly from them are unmarked.
* CIs are 95%. Continuous quantities carry percentile-bootstrap intervals;
  proportions carry Wilson score intervals. Both are seeded, so a figure
  regenerates identically.

---

## 1. Vocabulary and framework

**The hold ratio has one definition.** A row's hold ratio is the **median of the
per-run ratio** of its dispersion under a hostile setting to its own dispersion
on flat ground, paired by run index against the same seed base, with a percentile
bootstrap on that same quantity. The ratio-of-medians form used by §§6, 7, 9 and
13 as first written is **retired**; its values are kept in §12.1 for traceability
and appear nowhere else. Two reasons: the interval is then computed on the
quantity reported rather than on a different one, and the paired form is what
§§14–21 and every committed figure script already use. The largest disagreement
between the two forms was 2.7% (2.208 against 2.149) and no claim changes sign.

**A decomposition is not a hold ratio.** The objective-versus-terrain split in
§13 is a statement about *levels* of dispersion, and it decomposes only because
medians of levels are additive. It is therefore reported from medians and is
unaffected by the change above; the paired data contributes a significance test
on the terrain term instead. Per-run *shares* are not available: the per-run gap
is negative in 11 of 100 runs at 0.74 m and 31 of 100 at 1.5 m, so a median of
per-run shares is an artefact of sign changes in its own denominator.


### 1.1 The capability vector

`c = (S, M, A, K)`, from the build doc §2.1:

| symbol | meaning | notes |
|---|---|---|
| `S` | **sensor states per timestep**, not bits | Gauci's binary line-of-sight sensor is `S = 2`. A ternary sensor (nothing / robot / pursuer) is `S = 3`. A binary LOS sensor crossed with a binary terrain bit is `S = 2 × 2 = 4`. Report states; report log₂ only as a secondary summary. |
| `M` | persistent memory bits carried across timesteps | One bit of hysteresis ("saw a robot last step") is `M = 1`. |
| `A` | arithmetic flag | `A = 0` means a pure lookup table. Every row in this paper has `A = 0`. |
| `K` | **communication bits broadcast per timestep** | Any "I can tell a neighbour is fleeing" cue is `K ≥ 1` on the sender *and* an extra sensor state on the receiver. It is not free and it is not sensing. |

**The ladder is a set of vectors, not a chain of supersets.** Some rows are
incomparable — two extra sensor states versus one memory bit — and the surface
handles that by being drawn per row rather than along an ordering. The paper must
not present a ladder.

**Cost ordering.** The repository does not define a scalar cost over `c`. Rows
are compared as vectors, and where two rows are incomparable the paper says so.
The one ordering that is used is *within* a component: `S = 2` is cheaper than
`S = 4` at equal `M, A, K`.

### 1.2 Environment dials

Three, from the build doc §2.4. Exact parameterisations are in §3 of this file.

| dial | symbol | what it varies |
|---|---|---|
| occlusion | `θ_occ` | false-negative and false-positive rates on the LOS sensor, spatially correlated |
| terrain | `θ_terr` | per-wheel traction field amplitude `θ_m` and slope angle `α`, with correlation length `λ` reported alongside |
| pursuer | `θ_pred` | speed ratio `ρ`, sensing range `r_p`, confusion `κ`, handling time `h` |

### 1.3 Thresholds and the figure

The deliverable is **not** a one-step frontier. For each capability row, plot the
performance surface over the hostility dial(s), then draw the threshold contours
`P = T` on it. Several contours on one panel (T = 0.7, 0.8, 0.9) show how the
"minimum" depends on where the bar is set, which is the visual answer to
"minimality is ill-defined". The frontier `c*(θ)` is then read off as the lowest
row whose contour still encloses `θ`.

`T` and the metric it is set on are **fixed per paper and pre-registered**
(`docs/statistics.md`). Reporting several contours is not a substitute for
pre-registering one: the contours show how the answer depends on the bar; the
pre-registered `T` *is* the bar.

**The primary metric is dispersion at τ**, in the swarm-centroid frame. This is a
binding choice, not a preference, and it was forced by measurement: across the
whole Idea A terrain grid the share of runs that *ever* reach a single cluster is
1.00 in every cell except one runaway corner, so a threshold set on "did they
aggregate" sees almost nothing while one set on dispersion sees a clean monotone
signal (correction #6; §2). A second measurement points the same way: over a link
distance from 2.2 to 6.0 body radii, median final dispersion does not move at all
(**1.3875** at every value, spread exactly 0) while the share of time reading as a
single cluster climbs from **0.475 to 0.967**. *(Corrected in freeze lift 1, F1:
the published figures were produced at `axle_length = 0.053`; see §13 rows 13–14
and `verification-report.md`. The invariance the claim rests on is unchanged —
the spread is exactly zero either way.)*

### 1.4 `c*(θ, n)` is a function of swarm size, and part of the answer is a theorem

Steinberg and Solovey (2024) prove that for **any** bimodal controller in this
class — memoryless, binary line-of-sight sensor, no communication — there exists
a swarm size `n` and an initial state for which it does not aggregate
(assumptions: plastic collisions, no noise, no slippage). So for one whole
capability row the minimum does not exist uniformly in `n`. `c*` must therefore
be written `c*(θ, n)`, and minimality in this class is a probabilistic and
size-dependent statement rather than a guarantee (correction #2).

### 1.5 The baseline rule, as it stands after §21

`c*(θ, n)` is reported against the **best known S = 2 controller per cell over
the candidate set**, not against the published constants alone. The candidate set
is fixed and is listed in §4 of this file. Every searched member carries †, so
the baseline itself is an upper bound.

**After §21 the baseline is not a named row.** Three searches differing only in
the optimiser seed returned controllers whose R₀ spans 7.47, 8.88 and 8.64 cm —
a 16.9% spread, outside the pre-registered 10% agreement rule — and whose
held-out dispersion intervals are disjoint in 4 of 12 cells. The rule in force is
therefore:

> The baseline in each cell is the **best of the three class-searched rows in
> that cell** — `S2-class-flat-s1 †`, `S2-class-flat-s2 †`, `S2-class-flat-s3 †`
> — and the row achieving it is named. The spread between the three is the
> baseline's **uncertainty** and is reported alongside, not averaged away. The
> published constants (`S2-gauci`) remain the only **enumerated** row and are
> kept as the reference the baseline is measured against.

**The candidate set is not the same for both jobs the baseline does, and after
experiment 2 (§23) it has to say so.** The rule above was written for one of them.

* **For a capability comparison** — "is any S = 4 row better than S = 2 here?",
  which is claim A1 — the S = 2 competitor is the **best of every S = 2 row
  evaluated in the cell, including single-condition rows**. That is the
  conservative choice: it makes S = 4 harder to beat, which is the right
  direction for an upper-bound claim. At experiment 2's cells this mattered —
  `S2-searched`, a single-condition row, **beat all three class seeds at both
  n = 10 and n = 50**, so it and not the class baseline is what A1's verdict is
  measured against.
* **For the `c*(θ)` baseline as a region** — claim C3 — the candidate set stays
  **the class rows**, and the spread between the three seeds is the region's
  width. That is the whole point of C3: a frontier drawn through one
  single-condition row measures overfitting to its training arena.

**These two do not contradict each other and the paper must not read as if they
do.** C1's cells are flat ground at three start radii and n = 50, where a
single-condition row is *worse* than the published constants — that is the
failure C3 exists to prevent. A1's cells are λ = 0.10 m, θ_m = 0.9 at the
training n and two others, where the same kind of row is the *strongest* S = 2
candidate available. Different cells, and a different job for the row: C1 asks
what a single-condition row does away from its training point, A1 asks what the
best available S = 2 row does at a point where one was trained.

Seed 1 is the row §19 originally named as the baseline and is the weakest of the
three by cell count (9 W / 2 L / 1 tied against the reference, where seeds 2 and 3
score 10/0/2 and 10/1/1). No seed dominates another head to head.

The rule exists because of a measured failure. §14 showed that a controller
searched at one operating point can be *worse than the published constants* at
another: two rows searched at n = 20, start radius 0.74 m are worse than Gauci's
on flat ground at n = 50 at every start radius tested, and one of them forms a
cluster in 34% of runs at four times the training radius against Gauci's 100%,
even at six times the trial length. A frontier drawn through a
single-condition-searched baseline measures how well the optimiser overfitted its
training arena, which is a third quantity on top of capability and parameters
(corrections #11 and #15).

### 1.6 Upper bounds, stated as a rule

From the build doc §2.2, and enforced in the code (`controller.rs`: an unlabelled
row defaults to the pessimistic assumption; every run record carries `provenance`
and `minimum_is_tight`; every sweep prints how many of its cells are non-tight):

* Gauci's 4-constant grid is exhaustive at its resolution, so that row alone is
  tight. At 8 constants the grid grows as resolution⁴ and is not enumerable —
  20⁸ ≈ 2.6 × 10¹⁰ points at Gauci's resolution.
* Wherever sep-CMA-ES is used, "no controller found meeting T" means **not
  found**. Every †-marked row in Ideas A and B is an upper bound on `c*(θ, n)`.
* Report the search budget per cell. Where feasible run two independent
  optimisers, or the same optimiser from independent seeds, and report their
  agreement (`docs/statistics.md`; done in §21).

The exact wording used in every figure in this repository, and which the paper
should reuse verbatim:

> † searched, not exhaustive — an upper bound.
> ‡ hand-designed, not searched — no evidence about the capability itself.

---

## 2. Robot and simulator model

Tier 1 is a purpose-built Rust simulator (`crates/swarm-core`). Tier 2 (ARGoS)
was never run; every number in this paper is Tier 1. Throughput on a release
build, 4 cores: ~0.25 s per trial at n = 20, τ = 600 s, dt = 0.1 s, with the
O(n²) sensor loop dominating.

### 2.1 Parameters, with sources

Every value below is taken from Gauci, Chen, Li, Dodd & Groß (2014), IJRR, and
is pinned by a test rather than by a comment.

| parameter | value | source |
|---|---|---|
| body | disk, **diameter 7.4 cm** (radius 0.037 m), mass 152 g | "the body of an e-puck is modeled as a disk of diameter 7.4 cm and mass 152 g" |
| inter-wheel distance (axle `ℓ`) | **5.1 cm** | same sentence. **The repository originally assumed 5.3 cm; this was found to be wrong and corrected**, and it is what the derived-quantity test caught. |
| wheel speed limits | independently settable in **[−12.8, +12.8] cm/s** | same sentence |
| control cycle | **0.1 s**, physics updated **10× per cycle** | stated in the paper |
| sensor | **zero-width ray** cast from the e-puck's front, returning the first body it intersects; **infinite range** | "the binary sensor was realized by projecting a line from the robot's front… simulated by casting a ray from the e-puck's front and checking the first item with which it intersects". The paper separately proves a sufficiently long range is necessary. |
| controller constants | `x* = (−0.7, −1.0, 1.0, −1.0)` | the published optimum |
| arena | unbounded, as in Gauci's simulation | metrics are taken in the swarm-centroid frame so any bulk translation is factored out |

Derived quantities, published and reproduced:

| quantity | published | reproduced to |
|---|---|---|
| state-0 turn radius `R₀` | **14.45 cm** | 5 × 10⁻⁵ m |
| state-0 angular rate `ω₀` | **−0.75 rad/s** | 5 × 10⁻³ rad/s |
| state-1 angular rate `ω₁` | **−5.02 rad/s** | 5 × 10⁻³ rad/s |

These three are held by `controller::tests::published_derived_quantities_reproduce`,
which ties the wheel constants, the body geometry and the kinematics together. It
is the strongest single check in the week-1 gate and it is what caught the
inter-wheel distance. It has been green at every commit since.

### 2.2 Integration and contact

* **Exact-arc integration.** Constant wheel speeds over a control step trace a
  circular arc, which is integrated in closed form. One period of the state-0
  constants closes to within 1 × 10⁻⁹ m and holds radius `R₀` throughout, and the
  result is independent of the timestep. Because the integration is exact,
  substepping a constant-wheel-speed arc is a **no-op**, which is why the
  paper's "physics 10× per control cycle" has no effect here.
* **Contact.** Positional relaxation with early exit at a residual-overlap
  tolerance. Measured on 25 robots after 600 steps, worst residual overlap as a
  share of body diameter: 5.0% (4 passes), 1.3% (8), 0.05% (16), 0.01% (32),
  0.01% (64). Converged by 32 passes, which is the default; a test holds the line
  at 0.1%. This is a positional projection, not contact dynamics — adequate for
  Tier 1, and the reason Tier 2 exists in the plan.
* **Reproducibility.** Runs are bit-for-bit reproducible from `(seed, run_index)`,
  and the environment fields draw from separate seed streams so changing `n` does
  not reshuffle the terrain.

### 2.3 Start radius and τ conventions

* Robots start uniformly in a disk. The default start radius is derived from a
  **coverage** parameter, `R_start = R_body · sqrt(n / coverage)` with
  `coverage = 0.05`, so initial density is constant across swarm sizes. At
  n = 20 this gives **R = 0.74 m**; at n = 50 it gives 1.17 m.
* Every sweep that varies the start radius **pins it explicitly**
  (`swarm.init.radius`), which breaks the constant-density convention on purpose:
  at a pinned 0.74 m, n = 50 is 2.5× the density of n = 20. This confound is
  named wherever it matters.
* τ = **600 s** for every terrain and aggregation sweep; τ = **120 s** for the
  pursuer sweeps, because at ρ = 1.5 with a long range a swarm is wiped out
  inside 120 s and both `capture_rate` and `survival_fraction` pin once that
  happens.
* τ = 600 s was checked, not assumed. Across n = 2 to 10, median final dispersion
  and the share ever forming a single cluster are flat from τ = 600 s to
  τ = 48 000 s — an eighty-fold range. Where a later experiment found 600 s
  binding (start radius 3.0 m under terrain), τ was extended to 1800 and 3600 s
  **for every row in that cell** and both readings reported.

### 2.4 Metrics

* **Dispersion** `u = 2·Σ|p_i − p̄|² / (n²R²)`, the Graham & Sloane normalised
  second moment Gauci et al. report, normalised so a perfectly packed cluster
  scores ~1. Translation- and rotation-invariant; scores a packed hexagonal
  lattice at O(1). **The exact constant has not been checked against the
  published figures** — see §9 and §12 of this file. Comparisons *between* cells
  share the normalisation and are unaffected.
* **Reach** (`ever_single_cluster`): whether the swarm ever formed one connected
  component during the run. This is the criterion the literature uses.
* **Hold** (`single_cluster` at τ, `fraction_time_single_cluster`): whether it is
  one component *at* τ, and for what share of the run.
* **Hold ratio**: dispersion at a hostile setting divided by the same row's
  dispersion on flat ground, paired by run index. Used wherever rows differ on
  clean ground, so that a row which simply aggregates better cannot masquerade as
  terrain-robust.
* Clusters link bodies closer than `cluster_link_radii × R_body` centre to
  centre, default **3.0 body radii**.

### 2.5 The Gauci reproduction, and the metric correction it forced

Week-1 gate status: **PASSED**, with the small-n criterion corrected.

| check | status |
|---|---|
| e-puck constants match | pass, **and one was wrong** — inter-wheel distance 5.1 cm, not 5.3 cm. Fixed. |
| published derived quantities reproduce | pass, to 5e-5 m and 5e-3 rad/s, pinned by a test |
| sensor model matches | pass — a zero-width ray from the front |
| control cycle matches (0.1 s) | pass, and shown irrelevant over a 50-fold range |
| published constants aggregate a swarm in a clean arena | pass (n ≥ 10) |
| dispersion of a packed cluster is O(1) | pass |
| aggregation improves monotonically with swarm size | pass (n = 10 → 100) |
| small swarms aggregate | pass **against the corrected criterion** |
| absolute dispersion matches the published curve | **not checked** — needs the paper's figures |

Clean-arena scaling, `configs/sweeps/gauci_scaling.toml`, 100 runs/cell, τ = 600 s:

| n | dispersion at t = 0 | dispersion at τ | ratio | **ever one cluster** | one cluster at τ | share of time |
|---|---|---|---|---|---|---|
| 2 | 8.09 | 8.84 | 1.09 | **0.88** | 0.15 | 0.10 |
| 5 | 16.93 | 5.30 | 0.31 | **0.98** | 0.09 | 0.05 |
| 10 | pairs still one cluster at τ, n = 2 | **0.15** | share of *time* as one cluster is 0.10 | — | validation §1 | `2441bfc` |
| 20 | occlusion: realised FN rate at nominal 0.6 (correlated), **median** | 0.89 | mean 0.856 | — | §1 | `24ca1ac` |
| 50 | 19.20 | 1.20 | 0.063 | **1.00** | 0.93 | 0.87 |
| 100 | 19.84 | 1.15 | 0.058 | **1.00** | 0.97 | 0.90 |

**The two-robot numbers, and why they matter.** The gate initially failed at
small `n` and stayed failed for two weeks across five hypotheses, all of which
were wrong. The cause was not in the simulator:

1. The check appealed to Gauci et al.'s Theorem 3, "two robots always aggregate".
   **That proof has since been disproven.** Steinberg and Solovey (2024) identify
   an unsound implicit assumption — that a distance condition `d ≤ 2(R+r)`
   guarantees subsequent aggregation, when two robots can satisfy it while
   travelling the same circular perimeter without ever seeing each other — and
   report the same controller failing to aggregate on **4.24%** of two-robot
   trials.
2. The literature's definition of aggregation is **reaching** a connected
   configuration, not being in one at τ. For a pair that is a difference of an
   order of magnitude: **93% of pairs here reach exact contact and only ~10% are
   still touching at τ**; the scaling table above reports 0.88 reaching against
   0.15 holding at n = 2.

Measured against the criterion the literature actually uses, this simulator
agrees with it: 88–98% of small swarms reach a single cluster, against the
~95.8% reported for this controller at n = 2. The reason the two columns diverge
is angular size — at contact the other robot subtends about 60°, so a robot is
frozen for a sixth of each rotation and backing away for the rest, while in a
dense cluster it is frozen most of the time and robots accumulate.

The methodological lesson recorded at the time: **when a reproduction fails,
check the claim before checking the code.** Four rounds of instrumentation went
into a discrepancy whose cause was a disproven theorem and a mis-specified
metric.

### 2.6 The five ruled-out hypotheses, kept as sensitivity results

All at the corrected inter-wheel distance. Three are useful in their own right.

* **H-A, angular aliasing of the ray** — ruled out. Half-FOV ∈ {ray, 0.05, 0.10,
  0.20} crossed with dt ∈ {0.1, 0.01}: no trend in either dial; n = 20 sits at
  1.34–1.42 throughout.
* **H-B, time budget** — ruled out. τ from 600 to 48 000 s: flat. *Open
  observation, recorded not claimed*: n = 3 and n = 4 reach a single cluster far
  less often (0.25–0.56) than n = 2 (0.88) or n = 5 (0.98), and the dip does not
  close with time. The tempting reading is Daymude et al.'s deadlock (proven for
  n > 3 under uniform deterministic motion); the simpler one is combinatorial.
  Distinguishing them needs the deadlock configurations checked directly and
  nothing downstream depends on it.
* **H-C, missing baseline actuation noise** — ruled out. Per-wheel Gaussian noise
  at 0–20% of max wheel speed: no benefit anywhere; n = 20 dispersion 1.41, 1.40,
  1.39, 1.45 and reach 1.00 at every level. **This result contradicts an
  assumption H1 rests on** and is one of the three independent nulls behind
  correction #5.
* **H-D, sensor cone too narrow** — refuted by the source, twice. It is not what
  Gauci did (a zero-width ray was already implemented), and under the corrected
  criterion widening the cone makes n = 2 *worse*: reach falls 0.90 → 0.17 as
  half-FOV goes 0° → 68.8°, before a degenerate 90° case where both robots freeze
  on sight. Kept because at n ≥ 10 field of view barely matters, which is worth
  knowing for a hardware track where a real camera is not a ray.
* **H-E, discretisation** — ruled out. dt from 0.002 to 0.1 s (0.6° to 28.8° per
  step): fifty-fold refinement changes nothing, and the coarse step is if anything
  better. Consistent with exact-arc integration making substeps a no-op.

### 2.7 Invariants held by the test suite

Checked by `cargo test` on every commit (96 Rust tests in `swarm-core`, 14 in
`swarm-cli`, 32 Python tests in the harness at the freeze commit):

* Exact-arc integration closes one state-0 period to 1e-9 m, timestep-independent.
* `R₀` is the controller's only intrinsic length scale: scaling both wheels
  equally leaves the turn radius invariant — the reason v1's scalar speed field
  could not break symmetry. Per-wheel scaling does change it.
* Terrain deforms the trajectory, not just its position: with linear drift
  removed, a slope stretches the state-0 loop along the fall line (+4.6% at 10°,
  growing with α), and a traction field alone deforms it; flat terrain leaves a
  circle to within 1e-6. A Galilean drift could do none of this.
* The sensor is a real line of sight: bodies ahead are seen, behind are not, a
  body off-axis by more than its angular half-width is missed, and a nearer body
  occludes a further one.
* Dispersion is translation- and rotation-invariant and scores a packed
  hexagonal lattice at O(1).
* Runs are bit-for-bit reproducible from `(seed, run_index)`.
* Time-resolved aggregates do not depend on the series being stored.
* Only enumerated rows report a tight minimum; an unlabelled row defaults to the
  pessimistic assumption.

---

## 3. Environment models

### 3.1 Terrain (Idea A)

Per wheel `w ∈ {L, R}`:

```
v_w  =  v_cmd,w · m_w(x, y)  −  g_eff · sin(α) · (ĥ · ŝ)
```

* `m_w(x, y) = clamp( 1 + θ_m · f(x, y), ≥ traction_floor )` — a per-wheel
  traction multiplier. **The two wheels sample the field at their own contact
  points**, so they generally differ, the curvature changes, and the state-0
  circle becomes a distorted loop.
* `g_eff · sin(α) · (ĥ · ŝ)` — gravity along the robot's heading `ĥ` on a slope
  of angle `α`. `g_eff` is phenomenological (units m/s: the speed gained rolling
  straight down a 90° slope) and was used at **0.4** in the Idea A sweeps.
  **Sign convention:** the build doc writes a minus sign with `ŝ` described as
  downhill, which would make a robot slow down pointing downhill. The repository
  keeps the minus sign and defines `slope_dir` as the **uphill** direction, so
  heading uphill costs speed and heading downhill gains it. Same equation,
  physical sign (ADR 0002).
* Optional per-wheel slip noise scaled by `|sin α|`; **zero in every sweep
  reported here**.

**Why v1's model was replaced, and the control that confirms it.** A scalar speed
field scaling both wheels equally keeps the instantaneous centre of rotation
fixed: `v' = mv`, `ω' = mω`, so `dp/dθ = v/ω` is independent of `m` and the robot
traces the *same* circle at a position-dependent rate. A constant drift is a
Galilean shift leaving every line-of-sight reading unchanged. Both facts are
pinned by tests, and §6 measures the difference directly (see the ledger).

**The field generator.** Lattice value noise with quintic (C²) interpolation:
stateless, exactly reproducible from a seed, no grid to allocate. Output is in
`[−1, 1]` but is **not uniform** — it is bell-shaped and concentrated near zero.
The correlation length `λ` is the lattice spacing in metres; features are roughly
that size. Median `|f|` over the field is **0.3476** (max 0.9998, p99 0.9332),
measured across 40 seeds and 1.6 M samples and pinned by a test. There is no
closed-form correlation function; `λ` is a lattice spacing, not a Gaussian
correlation length, and the paper should say so.

**The θ_m ceiling, and the clip.** The field reaches `|f| = 1`, so at `θ_m = 1`
the multiplier `1 + θ_m·f` can reach zero: a wheel stalls outright and the robot
pivots, which is a different dynamical regime and not terrain deformation. All
terrain sweeps are therefore **cut at θ_m = 0.9**, below the `1/max|f| = 1.0` at
which that becomes possible (correction #10). A floor of `m ≥ 0.05` is
implemented as a safety net and is verified never to bind inside the swept range.
The θ_m = 1.25–1.5 band visible in an early H2 figure was stall, not terrain, and
was **removed from the swept range rather than explained away**.

**The terrain bit** (the S = 4 row's extra state): `|m(x,y) − 1| > θ_bit` at the
robot centre, with `θ_bit` defaulting to the field median `θ_m · 0.3476`. A bit
that is almost always the same value carries nothing, so the threshold is chosen
to split ~50/50; a test holds the split between 0.4 and 0.6 across the amplitude
range.

**The two dials are not interchangeable.** At matched degradation, slope alone at
15° reaches 1.51 and traction alone at θ_m = 0.5 reaches 1.63 — comparable — but
the runaway corner belongs to traction, and it is traction that pushes the swarm
past aggregating at all. Slope keeps the swarm together and drags it; traction
breaks it up.

### 3.2 Pursuer (Idea B)

The v1 pursuer — nearest target, perfect perception, unbounded range — made a
tight cluster the *cheapest* thing to hunt, so aggregation scored as the worst
possible strategy and the metric never saw dilution. The corrected family adds
perception limits, under which aggregation has two mechanisms by which it *can*
protect: **search cost** (a pursuer that sees nothing must search, and time
searching is time not capturing) and **confusion**.

| dial | symbol | value(s) used | definition |
|---|---|---|---|
| speed ratio | `ρ` | **1.5** throughout | pursuer speed / robot max speed. ρ > 1 means a locked target cannot escape. |
| sensing range | `r_p` | 0.10, 0.20, 0.35, 0.60, 1.00 m | omnidirectional within `r_p`, **not** a line-of-sight ray |
| confusion | `κ` | 0, 0.5, 1.0, 2.5, 5.0 (and 3.0 in the Pareto cells) | `p_lock = 1 / (1 + κ · n_local)`, after Olson et al. (2013), with `n_local` counted inside `confusion_radius = 0.5 m` |
| handling time | `h` | 5.0 s (§5); **0.39 s and 1.93 s** (§8, §12) | Holling's: seconds the pursuer is out of action after a capture |
| targeting | — | **nearest** | alternatives implemented but unused: fewest-neighbours (edge-picker), random-visible |
| search | — | **correlated random walk**, heading diffusion 1.0 rad/s std | alternative implemented but unused: Archimedean spiral, pitch 0.05 m/rad |
| capture | — | centre-to-centre **0.08 m** | |
| pursuer count | — | **1** | |

**The pursuer's asymmetry is deliberate**: the robots are the minimal agents
under study; the pursuer is part of the environment, so it gets omnidirectional
perception within its range.

**Handling time is required, not optional** (correction #7). With capture free on
contact, a packed cluster is a buffet — the pursuer takes one robot per control
step and twenty robots are gone in two seconds — so aggregation is maximally bad
under any metric, which is the v1 failure mode reappearing one level down.
Handling time is what makes dilution exist at all. The values used are principled
rather than round: the pursuer's own travel time between touching neighbours in a
formed cluster is 7.4 cm at ρ·v_max = 19.2 cm/s = **0.385 s**, so h = 0.39 s is
comparable to it and h = 1.93 s is 5× it.

**`r_p` must be read against the start radius, and the paper must print both.**
The swarm starts inside a disc of radius **R = 0.74 m** at n = 20, so:

| r_p (m) | 0.10 | 0.20 | 0.35 | 0.60 | 1.00 |
|---|---|---|---|---|---|
| r_p / R | 0.14 | 0.27 | 0.47 | 0.81 | **1.35** |

`r_p ≥ R` is the **perfect-perception corner**: the pursuer sees the whole
starting swarm from anywhere in it, so that column is not the hard end of a
difficulty axis, it is the degenerate one. Read as metres alone, the top of the
axis looks like the most demanding cell; it is the one where hiding is
impossible. Every Idea B figure in the repository ticks its `r_p` axis in both
units, draws the boundary at R = 0.74 m, and colours the ticks past it; the rule
is enforced in the plotting layer (`label_pursuer_range`) so it cannot be
forgotten, and it no-ops when the start radius is itself swept.

**Saturation.** `capture_rate` and `survival_fraction` both pin once a swarm is
wiped out. τ = 120 s keeps survivors in most cells; where they do not,
`time_to_wipeout` is the readable measure and is reported instead. 8.8% of runs
in §5 and 29% in §8 ended in a wipeout, and those shares are stated rather than
averaged over.

### 3.3 Occlusion

Implemented and run once, as the week-3 harness shakedown (§1 of the ledger).
Two rates applied to the line-of-sight reading — `fn_rate` (a genuine detection
is dropped) and `fp_rate` (an empty reading reports a robot) — both optionally
**spatially correlated**, with `correlation_amplitude` modulating the local rate
by a smoothed field of correlation length `correlation_length`. Setting the
amplitude to zero recovers i.i.d. dropout as the control.

The modulation is multiplicative and clamped, so the mean *realised* rate is
close to the nominal but not equal to it; `realised_fn_rate` is on every run
record. **This is not a cosmetic detail**: at a nominal 0.6 the realised rate is
0.89, because the correlated field is sampled where the robots actually are and a
cluster that settles in a bad patch draws its readings from that patch.

**Was it ever run?** Yes — once, `configs/sweeps/occlusion_shakedown.toml`, and
it is §1 of the ledger. It was never revisited, no capability row was searched
under it, and it contributes one result (correlated and i.i.d. dropout must be
compared at matched *realised* rate) plus one figure pair. The paper can use it
as a methods warning about spatially varying dials in general, which is how the
repository uses it.

---

## 4. Controller families

Every row that ever appeared in a figure. `R₀` is the state-0 turn radius,
computed from the row's own axle length where that was overridden. Wheel
constants are fractions of the ±12.8 cm/s limit, given as (left, right) per
sensor state.

### 4.1 The aggregation rows (Idea A and the methodology sections)

| row | `c = (S,M,A,K)` | origin | state-0 constants | R₀ | axle | mark |
|---|---|---|---|---|---|---|
| S2-gauci / M0-gauci / base / per-wheel / body-base | (2,0,0,0) | Gauci et al. 2014, exhaustive grid | (−0.7000, −1.0000); state 1 (+1.0000, −1.0000) | 14.45 cm | 5.1 cm | tight |
| M1-hysteresis | (2,1,0,0) → 4 table rows | hand-written | Gauci's tiled across the memory bit | 14.45 cm | 5.1 cm | ‡ |
| S2-searched / S2-rough | (2,0,0,0) | searched †, θ_m = 0.9, λ = 0.10 m | (−0.2852, −0.9495); state 1 (+0.9354, −0.2262) | **4.74 cm** | 5.1 cm | † |
| S2-flat | (2,0,0,0) | searched †, θ_m = 0 | (−0.3289, −0.8923); state 1 (+0.9983, −0.6589) | **5.53 cm** | 5.1 cm | † |
| S4-terrain / S4-searched | (4,0,0,0) | searched † (cold), θ_m = 0.9 | (−0.2364, −0.5198, +0.7978, −0.4064 \| −0.1863, −0.9657, +0.9310, −0.4505) | 6.80 cm (smooth) / 3.8 cm (rough) | 5.1 cm | † |
| S4-warm | (4,0,0,0) | searched †, warm-started at `[S2-rough \| S2-rough]` | (−0.2508, −0.6935, +0.6144, −0.3189 \| −0.1342, −0.9476, +0.8290, −0.2794) | 5.44 cm | 5.1 cm | † |
| S4-composite | (4,0,0,0) | hand-built switch: bit 0 → Gauci, bit 1 → S2-rough | as above | 14.45 cm (bit 0) | 5.1 cm | ‡ |
| **S2-class-flat** | (2,0,0,0) | **class-searched †**, θ_m = 0, six conditions | (−0.4330, −0.8820); state 1 (+0.7924, −0.8865) | **7.47 cm** | 5.1 cm | † |
| S2-class-rough | (2,0,0,0) | class-searched †, θ_m = 0.9, six conditions | (−0.2491, −0.9093); state 1 (+0.8620, −0.6283) | 4.47 cm | 5.1 cm | † |
| S2-class-rough-tau | (2,0,0,0) | class-searched †, θ_m = 0.9, τ = 3600 s at the 3.0 m conditions | (−0.2367, −0.8740); state 1 (+0.7398, −0.2404) | 4.44 cm | 5.1 cm | † |

Derived kinematics for the five rows the methodology sections compare
side by side (forward speed and rotation rate of the blind state):

| row | state | constants | R₀ | forward speed | rotation rate |
|---|---|---|---|---|---|
| S2-gauci | 0 (blind) | (−0.7000, −1.0000) | 14.45 cm | −10.88 cm/s | −0.753 rad/s |
| | 1 (seen) | (+1.0000, −1.0000) | 0 (spin) | 0 | −5.020 rad/s |
| S2-flat † | 0 | (−0.3289, −0.8923) | 5.53 cm | −7.82 cm/s | −1.414 rad/s |
| | 1 | (+0.9983, −0.6589) | 0.52 cm | +2.17 cm/s | −4.159 rad/s |
| S2-rough † | 0 | (−0.2852, −0.9495) | 4.74 cm | −7.90 cm/s | −1.667 rad/s |
| | 1 | (+0.9354, −0.2262) | 1.56 cm | +4.54 cm/s | −2.915 rad/s |
| **S2-class-flat †** | 0 | (−0.4330, −0.8820) | **7.47 cm** | −8.42 cm/s | −1.127 rad/s |
| | 1 | (+0.7924, −0.8865) | 0.14 cm | −0.60 cm/s | −4.214 rad/s |
| S2-class-rough † | 0 | (−0.2491, −0.9093) | 4.47 cm | −7.41 cm/s | −1.657 rad/s |
| | 1 | (+0.8620, −0.6283) | 0.40 cm | +1.50 cm/s | −3.741 rad/s |
| S2-class-rough-tau † | 0 | (−0.2367, −0.8740) | 4.44 cm | −7.11 cm/s | −1.599 rad/s |
| | 1 | (+0.7398, −0.2404) | 1.30 cm | +3.20 cm/s | −2.460 rad/s |

Pairwise L2 distances in constant space:

| pair | L2 |
|---|---|
| S2-flat ↔ S2-rough | 0.443 |
| S2-flat ↔ S2-gauci | 0.516 (0.515 recomputed) |
| S2-rough ↔ S2-gauci | 0.882 |
| S2-gauci ↔ S2-class-flat | **0.376** |
| S2-gauci ↔ S2-class-rough | 0.607 |
| S2-flat ↔ S2-class-flat | 0.324 |
| S2-flat ↔ S2-class-rough | 0.162 |
| S2-rough ↔ S2-class-flat | 0.695 |
| S2-rough ↔ S2-class-rough | 0.412 |
| S2-class-flat ↔ S2-class-rough | 0.326 |
| S2-class-rough ↔ S2-class-rough-tau | 0.408 |
| S2-gauci ↔ S2-class-rough-tau | 0.936 |
| S4-warm ↔ its own start point | 0.464 (halves diverged by up to 0.254) |

### 4.2 The geometry rows (hand-picked constants, ‡, used to break confounds)

All are Gauci's table with the state-0 forward constant and/or the axle changed,
so that one length scale moves while another is held.

| row | state-0 constants | axle | R₀ | what it isolates |
|---|---|---|---|---|
| axle-half-R0-same ‡ | (−0.8378, −1.0) | **2.55 cm** | 14.45 cm | axle at fixed R₀ |
| axle-x2-R0-same ‡ | (−0.4783, −1.0) | **10.20 cm** | 14.45 cm | axle at fixed R₀ — **wheel contacts outside the 7.4 cm body; a numerical device, not a buildable robot** |
| R0-half-axle-same ‡ | (−0.4783, −1.0) | 5.10 cm | **7.23 cm** | R₀ at fixed axle |
| R0-x2-axle-same ‡ | (−0.8378, −1.0) | 5.10 cm | **28.89 cm** | R₀ at fixed axle |
| R0-07.7cm ‡ / R0-14.5cm / R0-23.0cm ‡ / R0-48.5cm ‡ | (−0.5 / −0.7 / −0.8 / −0.9, −1.0) | 5.10 cm | 7.65 / 14.45 / 22.95 / 48.45 cm | the first, coarser R₀ scan |
| body-half ‡ / body-base / body-x2 ‡ | Gauci's | 5.10 cm | 14.45 cm | **body diameter** 3.7 / 7.4 / 14.8 cm at fixed R₀ and axle. At 3.7 cm the 5.1 cm axle puts the wheel contacts outside the body; both non-default sizes are numerical devices. |
| per-wheel / scalar-centre | Gauci's | 5.10 cm | 14.45 cm | how the traction field is *sampled*, nothing else |

### 4.3 The pursuer rows (Idea B) — all hand-designed except B0

| row | `c` | table (per sensor state, ×(memory)) | R₀ (state 0) | mark |
|---|---|---|---|---|
| B0-blind | (2,0,0,0) | Gauci's | 14.45 cm | tight |
| B1-ternary | (3,0,0,0) | nothing → (−0.7,−1.0); robot → (+1.0,−1.0); pursuer → (−1.0,−1.0) | 14.45 cm | ‡ |
| B2-ternary-side | (5,0,0,0) | as B1 plus pursuer-left → (−1.0,−0.6) and pursuer-right → (−0.6,−1.0) | 14.45 cm | ‡ |
| B3-ternary-memory | (3,1,0,0) → 6 table rows | B1 plus a bit holding "saw the pursuer" for one extra step | 14.45 cm | ‡ |
| **D-dispersive** | (3,0,0,0) | nothing → (−0.95,−1.0); **robot → (−0.95,−1.0)** — identical, so a robot never stops for a neighbour; pursuer → (−1.0,−1.0), byte-identical to B1's | **99.45 cm** | ‡ |
| B4 | (3,0,1,0) | **never run** — communication is not wired, `rx` is held at 0, so a K = 1 row would silently behave as K = 0 | — | — |

The design rationale for B1–B3, recorded at the time: state-0 wheel speeds are
already backwards, so "flee" is to back away at full speed from whatever the
sensor is pointing at. Whether a search finds something better was left to a
later paper; these rows say whether it is worth looking.

**D differs from B1 in exactly one respect** — the spatial strategy — which is
what makes it a control for "does aggregation cause the survival, or does the
pursuer's poor perception?".

### 4.4 Search protocol

Every searched row in this paper used the same optimiser and the same discipline.

* **Optimiser: sep-CMA-ES** (Ros & Hansen 2008), diagonal covariance. Named
  precisely because it matters: the separable variant cannot exploit correlations
  between constants, so it is a *weaker* searcher than full CMA-ES and a row it
  fails to improve is correspondingly weaker evidence. That direction is the safe
  one — a weaker searcher loosens an upper bound, it never falsely tightens it.
* **Box constraint.** Constants are constrained to [−1, 1]; candidates outside
  are repaired to the box and charged a quadratic penalty (×10) for the repair
  distance, so the optimiser is not rewarded for drifting out.
* **Objective: the median** over `runs_per_eval` trials, matching how results are
  reported elsewhere. A mean would sit between the two modes of a bimodal cell.
* **Population size** follows the standard formula, `λ = 4 + ⌊3 ln n⌋`: 8 for
  four constants, 10 for eight.
* **Seed discipline.** The search runs on **training seeds**; the row is then
  evaluated on a **disjoint** seed range (evaluation base 20260904). Reporting
  the training objective as the result would be reporting the minimum of a noisy
  sample.

| row | budget (evals × runs) | sim runs | optimiser seed | training seed base | training condition |
|---|---|---|---|---|---|
| S2-searched / S2-rough | 600 × 12 | 7 200 | 11 | 900 000 | θ_m = 0.9, λ = 0.10 m, n = 20, R = 0.74 m, τ = 600 s |
| S2-flat | 600 × 12 | 7 200 | 11 | 900 000 (**same as S2-rough, deliberately**) | θ_m = 0, otherwise identical |
| S4-terrain (cold) | 600 × 12 | 7 200 | 11 | 900 000 | θ_m = 0.9 |
| S4-warm | 600 × 12 | 7 200 | 11 | 950 000 | θ_m = 0.9, warm-started at `[S2-rough \| S2-rough]` |
| S2-class-flat | **1200 × 12** | 14 400 | 1 (and 2, 3 in §21) | 910 000 | six-condition class, θ_m = 0 |
| S2-class-rough | **1200 × 12** | 14 400 | 1 | 920 000 | six-condition class, θ_m = 0.9 |
| S2-class-rough-tau | **1200 × 12** | 14 400 | 1 | 920 000 (**same as S2-class-rough, deliberately**) | six-condition class, θ_m = 0.9, τ = 3600 s at the 3.0 m conditions |

**The class objective.** With one training condition the objective is the median
final dispersion over 12 runs — exactly the single-condition objective. With
several it is the **geometric mean of the per-condition medians**, for two
reasons: median dispersion across the class runs from about 1.2 to tens, so an
arithmetic mean (or a median over pooled runs) is the hardest condition wearing a
disguise and lets the optimiser abandon the rest of the class; and the geometric
form reduces exactly to the single-condition objective when the class has one
member, so a class search and a fixed-condition search are one procedure at two
class sizes rather than two protocols. Runs are split evenly across conditions,
each condition drawing its own disjoint block of run indices, so every candidate
is scored on identical (condition, seed) pairs.

**The class**: `swarm.init.radius ∈ {0.74, 1.5, 3.0} m × swarm.n ∈ {20, 50}`, six
conditions, 2 of the 12 runs each. The budget was **doubled** relative to the
single-condition searches because the same four constants are fitted to six
conditions instead of one; giving both the same budget would confound "no
transferring controller exists" with "the class search was not given enough
evaluations to find one".

**Honest re-scores (the winner's-curse gap).** The training objective is the
minimum of a noisy sample and must not be quoted as a result. Where the gap has
been measured:

| row | reported training objective | honest re-score | note |
|---|---|---|---|
| S4-warm † | **1.2595** | — | better than the cold S4 search's 1.3012 and the S2 search's 1.3009; on held-out seeds the advantage disappears entirely |
| S2-rough † | 1.3009 | — | |
| S4-terrain † (cold) | 1.3012 | — | |
| S2-flat † | 1.1701 | — | |
| S2-class-flat † (seed 1) | 1.2143 | — | |
| S2-class-rough † | 1.9302 | **2.3456** at 100 runs/condition on its own training seeds | |
| S2-class-rough-tau † | **1.6009** | **2.6553** at 100 runs/condition on its own training seeds | a gap of 1.05 in the objective's own units; the selection itself was corrupted, not only the printed number |

| S2-class-flat-s1 † (seed 1) | 1.2143 | **1.2338** | gap **+0.0194** |
| S2-class-flat-s2 † (seed 2) | **1.1927** | **1.2246** | gap **+0.0318** |
| S2-class-flat-s3 † (seed 3) | 1.2120 | **1.2301** | gap **+0.0181** |
| S2-gauci (reference, not searched) | — | 1.2905 | — |

The three flat-class gaps are 1.5–2.7%, an order of magnitude smaller than the
rough class's +1.05, and the *ordering* of the reported objectives survives the
re-score. That is the noise-floor account predicting its own boundary: on flat
ground every condition reaches a cluster in every run and a 2-run per-condition
median is a usable estimate; at θ_m = 0.9 it is not.

---

## 5. Experiment ledger

One entry per findings section, in order. Each gives the question as it was
posed, the design, the pre-registered rule and which branch fired, the headline
numbers with intervals, what the experiment changed, the figure and the script
that regenerates it, and the limitations recorded at the time. Superseded
readings are kept and marked.

Unless stated otherwise: n = 20, τ = 600 s, 100 runs/cell, evaluation seed base
20260904, λ = 0.10 m for terrain, start radius from the coverage rule (0.74 m at
n = 20).

---

### §1 — Week-3 shakedown: occlusion
**Commit** `e175acb`…`24ca1ac` (regenerated at `2441bfc`).
**Question.** At what false-negative rate does the zero-memory Gauci controller
fall below threshold, and does one bit of hysteresis restore it? Also: does the
sweep harness work?
**Design.** `configs/sweeps/occlusion_shakedown.toml`, two rows (M0 = Gauci
tight; M1 = one hysteresis bit, 8 constants, hand-written ‡) on a
(false-negative rate × spatial correlation) grid, 100 runs/cell.
**Rule.** None pre-registered; this was a harness shakedown.
**Headline.** Median final dispersion (clean baseline 1.43):

| FN rate | M0 (tight) | M1 hysteresis ‡ |
|---|---|---|
| 0.0 | 1.43 | 1.28 |
| 0.2 | 1.44 | 1.34 |
| 0.4 | 1.57 | 1.41 |
| 0.6 | 1.70 | 1.53 |
| 0.8 | 2.23 | 1.95 |
| 0.9 | 3.32 | 2.72 |

The memory bit helps everywhere, **including in the clean arena**, and the gap
widens with the dropout rate.

**The result that survived.** At matched *nominal* rate, correlated dropout looks
dramatically worse than i.i.d. — 4.15 against 1.70 at a nominal 0.6 — but the
realised rate at that nominal is **0.89**. Binned by *realised* rate (M0 row):

| realised FN | i.i.d. | correlated |
|---|---|---|
| 0.00–0.05 | 1.43 | 1.43 |
| 0.25–0.35 | 1.52 | 1.50 |
| 0.45–0.55 | 1.60 | 1.65 |
| 0.60–0.70 | 1.80 | 1.99 |
| 0.72–0.80 | 2.20 | 2.12 |
| 0.85–0.95 | 3.32 | **4.68** |
| 0.95–1.00 | — | 25.42 |

Below a realised rate of ~0.8 the two are within each other's spread; a genuine
extra penalty for spatial structure appears only above it, where the swarm can be
trapped in a patch that is effectively blind.
**Changed.** A standing rule: any dial whose intensity varies in space has a
realised value that depends on where the swarm ends up, and correlated and
i.i.d. versions must be compared at matched **realised** rate.
`realised_fn_rate` is on every run record for this reason.
**Figures.** `figures/occlusion_shakedown_curve.png`,
`figures/occlusion_shakedown_surface.png` (regenerate with
`harness/figures_occlusion_shakedown.py`; it was originally drawn by the
`swarm-figure` CLI, whose arguments were never recorded — see §10's note).
**Limitations.** M1 is a hand-written point in an 8-constant space (20⁸ ≈
2.6 × 10¹⁰ at Gauci's resolution), so any minimum read off it is an upper bound
and it is not even searched. Occlusion was never revisited.

---

### §2 — Idea A: terrain, first grid
**Commit** `2441bfc`…`c137593`.
**Question.** What does terrain do to aggregation, on both dials?
**Design.** `configs/sweeps/terrain_idea_a.toml`, `g_eff` = 0.4, λ = 0.15 m ≈ R₀,
slope α ∈ {0, 2.5, 5, 7.5, 10, 15}° × θ_m ∈ {0, 0.1, 0.2, 0.3, 0.5}, 100
runs/cell.
**Headline.** Median final dispersion (flat clean = 1.43):

| slope | θ_m = 0 | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| 0° | 1.43 | 1.40 | 1.41 | 1.49 | 1.63 |
| 2.5° | 1.39 | 1.41 | 1.43 | 1.46 | 1.74 |
| 5° | 1.42 | 1.44 | 1.46 | 1.47 | 1.76 |
| 7.5° | 1.47 | 1.43 | 1.47 | 1.50 | 1.78 |
| 10° | 1.42 | 1.49 | 1.48 | 1.55 | 1.93 |
| 15° | 1.51 | 1.52 | 1.59 | 1.68 | **2656** |

**Three results.** (i) *Terrain degrades cluster quality, not the ability to
aggregate*: reach is **1.00 in every cell** except the runaway corner, where it
is 0.52. (ii) *H1 is not supported*: the trend is monotone degradation on both
dials; the only hints in H1's direction are inside run-to-run spread and do not
survive a re-run. (iii) *The (15°, θ_m = 0.5) cell is outside the model's usable
range* — dispersion 2656 is the swarm spread over ~12 m; there
`g_eff·sin α = 0.104 m/s` against a 0.128 m/s wheel limit and traction reaches
1.5, so robots roll away downhill at different rates. It is a real consequence of
the model but a runaway regime, and is reported as the boundary of the dial range
rather than averaged into a trend.
**Changed.** Set the threshold on dispersion, not on a cluster count (correction
#6). Queued the fine H1 sweep.
**Figures.** `figures/terrain_idea_a_surface.png`,
`figures/terrain_idea_a_curve.png`.
**Limitations.** One λ; θ_m only to 0.5; the runaway corner excluded from trends.

---

### §3 — Idea A, H1: does a *small* amount of terrain help?
**Commit** `c137593`.
**Question.** H1 predicts small α and θ_m help, as motion noise did in Daymude et
al. Tested on its own terms rather than read off the corner of a grid built for
something else.
**Design.** `configs/sweeps/terrain_h1_fine.toml`, **200 runs/cell**, α ∈ {0,
0.5, 1, 1.5, 2, 3}° × θ_m ∈ {0, 0.02, 0.05, 0.1}, `g_eff` = 0.4, λ = R₀.
**Headline. Answer: no.** Median final dispersion with 95% bootstrap CIs, whole
grid between **1.385 and 1.430**; **0 of 23 non-baseline cells** has an interval
disjoint from the clean baseline's; every interval overlaps every other.
Representative row (α = 0°): 1.406 [1.389, 1.429], 1.388 [1.360, 1.406],
1.385 [1.371, 1.414], 1.414 [1.399, 1.436].
**Changed.** With the actuation-noise probe and §2, this is the third independent
null. **Correction #5**: H1 should be withdrawn, or narrowed to a mechanism this
model does not have. Daymude et al.'s mechanism is specific — noise "perturbs the
precise balancing of forces to allow robots to push past one another", breaking a
*contact deadlock* in a discrete model — and was never an argument that
perturbation aids exploration.
**Figures.** None committed.
**Limitations.** n = 20 only; the deadlock's existence in this continuous model
was never tested directly.

---

### §4 — Idea A, H2: does the terrain transition scale with R₀?
**Commit** `c137593` (first pass), `9b0b994` (powered).
**Question.** H2 predicts aggregation fails when trajectory deformation over one
state-0 circle exceeds a fraction of R₀ — so the transition should scale with R₀
and not with the wheel geometry or the swarm.
**Design.** Two sweeps. `terrain_h2_r0_scaling.toml` established that terrain
does nothing once λ > R₀ but had no transition to locate at θ_m ≤ 0.4 and could
not separate λ/R₀ from λ/axle. `configs/sweeps/terrain_h2_powered.toml` fixes
both: θ_m to 1.5, and five rows that hold one length scale fixed while varying
the other. Every row is scored against **its own** θ_m = 0 cell at the same λ.
**Headline.** Peak degradation and where it occurs, at θ_m = 0.7:

| row | axle | R₀ | peak λ | **λ/R₀** | λ/axle | peak degradation |
|---|---|---|---|---|---|---|
| axle-half-R0-same ‡ | 2.55 cm | 14.45 cm | 0.100 | **0.69** | 3.92 | 1.40 |
| base | 5.10 cm | 14.45 cm | 0.100 | **0.69** | 1.96 | 1.58 |
| axle-x2-R0-same ‡ | 10.20 cm | 14.45 cm | 0.100 | **0.69** | 0.98 | 1.34 |
| R0-half-axle-same ‡ | 5.10 cm | 7.22 cm | 0.050 | **0.69** | 0.98 | 1.17 |
| R0-x2-axle-same ‡ | 5.10 cm | 28.90 cm | 0.100 | 0.35 | 1.96 | 2.69 |

The peak sits at **λ/R₀ ≈ 0.7** for four of five rows across a four-fold range of
axle, while λ/axle over the same rows scatters from 0.98 to 3.92. The fifth row's
peak falls between grid points (λ/R₀ of 0.35 and 0.69 score 2.69 and 2.43), so
the λ grid sets that entry, not the physics.

The magnitudes settle it. At θ_m = 1.0: varying the **axle 4×** at fixed R₀ gives
peak degradation **2.21, 2.74, 3.18** — a spread of **44%**; varying **R₀ 4×** at
fixed axle gives **1.65, 2.74, 12.37** — a spread of **648%**. *(Corrected in
freeze lift 1, F2: produced before `e83675e` added `traction_floor = 0.05`; see
§13 rows 23–24. The ordering is unchanged and no claim changes — and this cell,
θ_m = 1.0, is outside the paper's stated range, where the traction multiplier's
minimum is 0.100, twice the floor, so the correction has no in-scope effect at
all.)*
**Branch.** H2 supported *as a statement about R₀ versus the axle*.
**Changed.** Narrowed the target for the anisotropy lemma to `f(R₀, λ)` with the
worst case near λ/R₀ ≈ 0.7. Also forced the θ_m ceiling: the sweep originally ran
to θ_m = 1.5, where every row degraded 6–14× and the ordering by R₀ collapsed —
that band is **stall, not terrain**, and was cut rather than explained
(correction #10).
**Superseded in part.** §15 and §17 show the peak is **not** proportional to R₀
when R₀ is varied inside one controller family and the λ grid is finer: the
result survives as measured (a peak, at λ/R₀ ≈ 0.5–0.7 for *this* R₀) and loses
its generalisation. §18 identifies the length as the body diameter. See the
claims register.
**Figure.** `figures/terrain_h2_powered.png`, `figures/terrain_h2_r0_scaling.png`.
**Limitations.** All five rows are hand-picked ‡. `axle-x2-R0-same` puts the
wheel contacts outside the 7.4 cm body and is a numerical device; it is also the
row that makes the 5% spread meaningful, so it stays in, labelled.

---

### §5 — Idea B, first pass: the pursuer with imperfect perception
**Commit** `9b0b994`; r_p normalisation added at `c65abe2`.
**Question.** How does survival move with the pursuer's perception limits, and
what does a sensor state buy?
**Design.** `configs/sweeps/pursuer_idea_b.toml`, n = 20, **τ = 120 s**, ρ = 1.5,
h = 5 s, R = 0.74 m, four rows on a **5 × 5** grid of r_p × κ, 100 runs/cell,
10 000 trials. 8.8% of runs ended in a wipeout.
**Headline.** Median survivors out of 20 (selected cells):

| κ | r_p (m) | r_p/R | B0 blind | B1 ternary ‡ | B2 ternary+side ‡ | B3 ternary+memory ‡ |
|---|---|---|---|---|---|---|
| 0 | 0.10 | 0.14 | 5.0 [4.0, 14.0] | 18.0 [17.0, 19.0] | 17.5 [15.0, 18.0] | 18.0 [16.0, 19.0] |
| 0 | 0.35 | 0.47 | 0.0 [0.0, 0.0] | 5.0 [5.0, 7.0] | 1.0 [1.0, 2.0] | 6.0 [5.0, 8.5] |
| 0 | 1.00 | **1.35 perfect perception** | 0.0 [0.0, 0.0] | 3.0 [3.0, 3.0] | 0.0 [0.0, 0.0] | 3.0 [3.0, 4.0] |
| 1 | 0.35 | 0.47 | 2.0 [1.0, 5.0] | 12.5 [8.0, 14.0] | 12.0 [10.0, 16.0] | 13.0 [11.0, 15.5] |
| 2.5 | 0.60 | 0.81 | 5.0 [5.0, 6.0] | 6.5 [6.0, 7.0] | 6.0 [6.0, 6.0] | 7.0 [6.0, 8.0] |
| 5 | 1.00 | **1.35 perfect perception** | 8.0 [8.0, 8.5] | 8.0 [8.0, 9.0] | 8.0 [8.0, 8.0] | 9.0 [8.0, 9.0] |

Median survival fraction over the whole grid: B0 **0.350** [0.300, 0.375],
B1 **0.650** [0.600, 0.700], B2 **0.450** [0.450, 0.525], B3 **0.700** [0.650,
0.750].
**Three readings.** (i) **One sensor state is worth more than everything else on
the capability axis**: going from S = 2 to S = 3 — telling a pursuer from a robot
— is the whole story; the blind row is wiped out at κ = 0 for every range beyond
0.10 m (0.14 R) while any row that can see the pursuer keeps 3–18. The memory bit
on top (B3) buys a further robot or two consistently, but nothing like as much.
(ii) **S = 5 scoring below S = 3 is a hand-design artefact, not a result** — B2's
table is a hand-written guess (‡) and a bad one; reporting it as "more sensing
hurts" would be the single easiest mistake to make with this data. (iii) **The
environment dials dominate the capability rows**: at κ = 5 every row keeps 8–9
robots at r_p = 1.0 m and 18–19 at r_p = 0.35 m, while at κ = 0, r_p = 0.35 m
they run 0 to 6.
**Changed.** Motivated §8's dispersive control (correction #8) and §12's two-axis
reporting (correction #12).
**Figure.** `figures/pursuer_idea_b_surface.png`
(`harness/figures_idea_b.py first_pass`).
**Limitations.** B1–B3 hand-designed ‡. **B4 (K = 1) was never run**:
communication is not wired, `rx` is held at 0, so a K = 1 row would silently
behave as K = 0, and adding a row that quietly does nothing is worse than leaving
it out. One ρ, one h, one n, one τ, one start radius.

---

### §6 — Idea A mechanism test: deformation, or speed heterogeneity?
**Commit** `e83675e`.
**Question.** A scalar speed field still makes robots in different places move at
different rates, which alone changes who meets whom. Is *that* the mechanism,
with curvature incidental?
**Design.** `configs/sweeps/terrain_mechanism.toml`, **paired seeds**: both rows
use the same placements and the same traction field and differ only in how the
field is sampled — per-wheel (the corrected model) versus scalar-centre (v1's).
100 runs/cell.
**Pre-registered rule.** If the scalar row reproduces the per-wheel row's peak
location **and** magnitude within CI, the mechanism is relative speed
heterogeneity and the curvature explanation is retired.
**Branch fired.** It does not reproduce; the curvature explanation **stands**.
**Headline.** Degradation relative to each row's own θ_m = 0 cell:

| λ | λ/R₀ | per-wheel, θ_m = 0.7 | scalar, θ_m = 0.7 | per-wheel, θ_m = 0.9 | scalar, θ_m = 0.9 |
|---|---|---|---|---|---|
| 0.0125 | 0.09 | 1.10 [1.06, 1.14] | 0.97 [0.96, 0.99] | 1.19 [1.11, 1.31] | 0.99 [0.97, 1.01] |
| 0.025 | 0.17 | 1.28 [1.19, 1.35] | 0.99 [0.98, 1.01] | 1.44 [1.39, 1.62] | 1.00 [0.99, 1.02] |
| 0.05 | 0.35 | 1.56 [1.44, 1.71] | 1.00 [0.98, 1.01] | 2.08 [1.84, 2.47] | 1.01 [0.99, 1.03] |
| **0.10** | **0.69** | **1.58 [1.48, 1.72]** | 0.96 [0.94, 0.98] | **2.21 [1.90, 2.41]** | 0.98 [0.96, 1.01] |
| 0.20 | 1.38 | 1.13 [1.09, 1.23] | 0.97 [0.94, 0.99] | 1.47 [1.32, 1.65] | 0.98 [0.97, 1.00] |
| 0.40 | 2.77 | 1.02 [1.00, 1.06] | 0.96 [0.94, 0.98] | 1.11 [1.06, 1.18] | 0.96 [0.94, 0.97] |

Pooled over every θ_m > 0 cell (1 800 runs each): per-wheel **1.175 [1.154,
1.190]**, scalar-centre **0.980 [0.976, 0.986]**. The scalar row has **no peak at
all** and is flat within [0.96, 1.01] across the entire grid.
**Changed.** Correction #9: the build doc's model correction is confirmed with a
paired control rather than an argument. Also fixed the θ_m ceiling at 0.9.
**Reported without explanation, per the rule.** The scalar row sits *slightly
below* 1.0 — pooled 0.980 [0.976, 0.986], an interval excluding 1.0. A pure
scalar speed field appears to aggregate about 2% *better* than flat ground. It is
not in H1's direction and 2% is at the edge of what this design resolves. On the
follow-up list, never chased.
**Figure.** `figures/terrain_mechanism.png`.
**Limitations.** One n, one τ.

---

### §7 — Idea A, H3: the first terrain-aware capability row
**Commit** `9af4707`.
**Question.** Past the transition, does a fifth sensor state (a binary terrain
bit) recover the threshold where re-tuning the original four constants does not?
**Design.** `configs/sweeps/terrain_h3_capability.toml`, three rows — S2-gauci
(tight), S2-searched †, S4-terrain † — evaluated on seeds **disjoint** from
training. Both searched rows got the same optimiser, the same budget (600 × 12 =
7 200 runs) and the same training seeds, so the difference between them is the
extra state and nothing else.
**Headline.** Hold ratio at λ = 0.10 m (λ/R₀ = 0.69):

| θ_m | S2-gauci | S2-searched † | S4-terrain † |
|---|---|---|---|
| 0.0 | 1.00 [0.98, 1.03] | 1.00 [0.99, 1.02] | 1.00 [0.99, 1.01] |
| 0.4 | 1.13 [1.09, 1.17] | 0.96 [0.95, 0.97] | 1.00 [0.99, 1.01] |
| 0.6 | 1.36 [1.26, 1.48] | 0.99 [0.97, 1.01] | 1.02 [1.01, 1.04] |
| **0.9** | **2.21 [1.90, 2.41]** | **1.10 [1.08, 1.15]** | **1.22 [1.16, 1.26]** |

Re-searching the same four constants removes almost all the degradation, 2.21 →
1.10. **Adding the terrain bit does not help**: 1.22 [1.16, 1.26] against 1.10
[1.08, 1.15], **disjoint intervals**.
**The control is the point.** Without S2-searched, the data reads as "the terrain
bit cuts degradation from 2.21 to 1.22" — a large apparent win for extra sensing,
and wrong.
**Honest statement.** Not "S = 4 is worse than S = 2", but **no S = 4 controller
better than the searched S = 2 one was found at equal budget**. 600 evaluations
over 8 constants is a thinner search per dimension than 600 over 4.
**Two secondary results.** (i) Reach is 1.00 across almost the whole grid and
moves only in the worst cell and only for the un-searched row: 0.86 [0.79, 0.93]
for S2-gauci against 1.00 and 0.99 for the searched rows. (ii) **The search
independently rediscovered H2**: state-0 R₀ is 14.45 cm (Gauci), 4.7 cm
(S2-searched), 6.8 cm (S4 smooth), 3.8 cm (S4 rough) — shrinking R₀ moves λ/R₀
from 0.69, the worst place, to 2.13. The optimiser was given no information about
R₀ or H2.
**Caveat recorded at the time.** The searched rows also aggregate tighter on flat
ground — 1.427 [1.399, 1.467] (gauci), 1.253 [1.234, 1.283] (S2-searched),
1.222 [1.211, 1.235] (S4) — so part of what the search bought is a better
controller in general. The hold ratio normalises each row by its own flat
baseline precisely so this cannot be read as terrain robustness.
**Method note.** Reach is a proportion and its median is 1 whenever the majority
succeed, so a median panel draws a flat line at 1 while the probability falls.
The first version of this figure did that and was wrong; the panels now use a
proportion CI.
**Figure.** `figures/terrain_h3_capability.png`.
**Limitations.** Equal budget across unequal dimensions; both S = 4 rows are
upper bounds; one λ, one training cell, n = 20.

---

### §8 — Idea B: is the blind row's survival attributable to aggregation?
**Commit** `c5203f4`; r_p normalisation at `c65abe2`.
**Question.** §5 read survival rising with confusion as dilution, but every row
there aggregated identically when no pursuer was in view, so nothing separated
"the swarm aggregated" from "the pursuer's perception is poor".
**Design.** `configs/sweeps/pursuer_dispersive.toml`, 5 × 5 grid of (r_p, κ) at
two handling times, 100 runs/cell, 15 000 trials. Three rows: B0-blind (tight,
aggregates, cannot see the pursuer), B1-ternary ‡ (sees and flees, aggregates),
**D-dispersive ‡** (sees and flees with a **byte-identical** pursuer response,
but a 99 cm state-0 arc so no cluster forms). D differs from B1 in exactly one
respect.
**Headline.** Mean survival fraction, κ = 0 → κ = 5:

| row | h = 0.39 s | h = 1.93 s |
|---|---|---|
| B0-blind | 0.180 → 0.548 (**×3.05**) | 0.144 → 0.592 (**×4.10**) |
| B1-ternary ‡ | 0.258 → 0.575 (×2.23) | 0.328 → 0.628 (×1.91) |
| D-dispersive ‡ | 0.530 → 0.638 (×1.20) | 0.591 → 0.666 (**×1.13**) |

The two aggregating rows multiply survival by 2–4× as confusion rises; the
dispersive row, with identical pursuer sensing, gains 13–20%. Confusion enters
the model only through `p_lock = 1/(1 + κ·n_local)` and only a clustered swarm
has a large `n_local`. **Handling time sharpens it in the predicted direction**:
B0's κ-response grows ×3.05 → ×4.10 as handling goes from comparable to the
inter-neighbour travel time to 5× it, while D's shrinks.
**But aggregation is a net liability over this grid.** Survival pooled over κ at
h = 1.93 s:

| r_p (m) | r_p/R | B0-blind | B1-ternary ‡ | D-dispersive ‡ |
|---|---|---|---|---|
| 0.10 | 0.14 | 0.90 [0.90, 0.95] | 0.95 [0.95, 0.95] | 0.90 [0.85, 0.90] |
| 0.20 | 0.27 | 0.85 [0.80, 0.85] | 0.85 [0.85, 0.90] | 0.75 [0.75, 0.78] |
| 0.35 | 0.47 | 0.00 [0.00, 0.23] | 0.55 [0.45, 0.65] | 0.65 [0.60, 0.65] |
| 0.60 | 0.81 | 0.00 [0.00, 0.00] | 0.05 [0.05, 0.05] | 0.50 [0.45, 0.50] |
| 1.00 | **1.35 perfect perception** | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.35 [0.30, 0.35] |

Beyond r_p ≈ 0.35 m (0.47 R) the dispersive row wins by a lot. Confusion narrows
the gap — mean survival at κ = 5 is 0.592 (B0), 0.628 (B1), 0.666 (D) — but does
not close it. **Two of the five columns are at or past half the start radius and
one is the perfect-perception corner**, so the grid's upper half is deliberately
brutal.
**Saturation, stated rather than hidden.** 29% of all runs ended with the swarm
wiped out, concentrated exactly where the claim is strongest: B0 loses the whole
swarm in 72% of runs at κ = 0, falling to 27% at κ = 5, while D wipes out in ≤ 1%
anywhere. Time to wipeout at r_p = 0.35 m, h = 1.93 s: κ = 0 → 46.6 s (n = 94)
B0, 70.2 s (19) B1, never D; κ = 1 → 64.4 s (71), 82.6 s (26), never; κ = 2.5 →
88.8 s (8), 102.4 s (3), never; κ = 5 → never for all three.
**Changed.** Corrections #7 (handling time is required) and #8 (a dispersive
control row belongs in the design).
**Figures.** `figures/pursuer_dispersive_kappa.png`,
`figures/pursuer_dispersive_surface.png` (`harness/figures_idea_b.py dispersive`).
**Limitations.** B1 and D are hand-designed ‡ and support a claim about *spatial
strategy*, not about what S = 3 sensing can achieve.

---

### §9 — Does re-tuning move the problem or solve it?
**Commit** `f7376de`.
**Question.** S2-searched was tuned at exactly one point — the worst cell H2
found — and §7 only ever evaluated it on terrain. A controller tuned at the worst
cell can win there by giving up performance elsewhere; if such a trade-off
exists, the terrain bit has an obvious job.
**Design.** `configs/sweeps/terrain_retune_cost.toml`, λ = 0.10 m fixed, θ_m
swept 0 → 0.9 in eight steps, four rows including **S4-composite ‡**, a hand-built
switch (bit 0 → Gauci, bit 1 → S2-searched).
**Pre-registered rule.** Two branches anticipated at θ_m = 0: S2-searched matches
Gauci within CI, or is worse with disjoint CIs.
**Branch fired: neither.** S2-searched is **strictly better** on flat ground —
1.253 [1.234, 1.283] against 1.427 [1.399, 1.467], disjoint, 12.2% lower — on
ground it was never tuned for.
**Headline.** Absolute final dispersion:

| θ_m | S2-gauci | S2-searched † | S4-composite ‡ | S4-searched † |
|---|---|---|---|---|
| 0.00 | 1.427 [1.399, 1.467] | 1.253 [1.234, 1.283] | 1.427 [1.399, 1.467] | 1.222 [1.211, 1.235] |
| 0.30 | 1.521 [1.470, 1.568] | 1.211 [1.199, 1.226] | 1.476 [1.424, 1.527] | 1.219 [1.210, 1.230] |
| 0.60 | 1.943 [1.799, 2.112] | 1.235 [1.220, 1.264] | 1.638 [1.562, 1.783] | 1.248 [1.239, 1.268] |
| 0.90 | **3.150 [2.716, 3.439]** | **1.383 [1.350, 1.441]** | 1.999 [1.861, 2.143] | 1.486 [1.424, 1.535] |

Disjoint at **every one of the eight θ_m values**. Reach at θ_m = 0.9: S2-gauci
**0.86 [0.78, 0.91]**, S2-searched 1.00 [0.96, 1.00].
**The composite demonstrates flatness constructively.** It is **worse than the
S = 2 row it is built from at every θ_m** — 1.999 against 1.383 at θ_m = 0.9 —
because half the time it deliberately selects the worse of its two behaviours.
Its θ_m = 0 value reproduces Gauci's exactly (1.427 [1.399, 1.467]), which is the
internal consistency check: on flat ground the bit is never set, so the composite
*is* Gauci.
**Conclusion at the time.** `c*(θ_terr)` is **flat in capability** over
0 ≤ θ_m ≤ 0.9 at λ/R₀ = 0.69: `c = (2,0,0,0)` suffices at every point. What moves
is the parameter setting inside a fixed capability.
**Superseded in its explanation.** "Re-tuning solves it" was right about the
direction and wrong about the cause — see §13 and §14, and correction #11 as
rewritten. The flatness in *capability* stands.
**Figure.** `figures/terrain_retune_cost.png`.
**Limitations recorded at the time.** One λ; both S = 4 rows are upper bounds and
the composite is not even that; everything at n = 20.

---

### §10 — Warm-started S = 4 search
**Commit** `6989a91` (lint fix `1da65d8`).
**Question.** §7's equal-budget-over-unequal-dimensions objection: did the S = 4
row lose on search effort rather than on capability?
**Design.** `configs/sweeps/terrain_warm_s4.toml` from
`results/search_s4_warm.json`. The search starts at `[S2-searched | S2-searched]`
— an eight-constant table whose halves are equal, i.e. an S = 4 controller that
ignores its own terrain bit. The optimiser therefore begins holding the S = 2
optimum and can only be asked whether *using* the bit beats *not* using it. Same
optimiser, same budget (600 × 12), training seeds 950 000, disjoint from the cold
search's 900 000 and from the evaluation seeds.
**The search did move**: L2 0.464 from its start, halves diverging by up to
0.254, so the found controller genuinely uses the bit.
**Headline.** Absolute final dispersion on held-out seeds:

| θ_m | S2-searched † | S4-searched † (cold) | S4-warm † |
|---|---|---|---|
| 0.00 | 1.253 [1.234, 1.283] | 1.222 [1.211, 1.235] | 1.216 [1.204, 1.226] |
| 0.45 | 1.212 [1.201, 1.222] | 1.212 [1.205, 1.224] | 1.218 [1.203, 1.227] |
| 0.75 | 1.322 [1.280, 1.358] | 1.330 [1.288, 1.366] | 1.297 [1.273, 1.340] |
| **0.90** | **1.383 [1.350, 1.441]** | 1.486 [1.424, 1.535] | **1.412 [1.349, 1.503]** |

At the peak cell the intervals **overlap** and the point estimate is 2.1%
*worse*. Given the S = 2 optimum as a starting point and equal budget, using the
terrain bit did not improve on ignoring it. The warm start does help relative to
the cold S = 4 search (1.412 against 1.486), which is what a better starting
point should do; it just does not get past S = 2.
**The winner's-curse demonstration.** The warm search's *training* objective was
**1.2595**, better than the cold search's 1.3012 and the S = 2 search's 1.3009.
On held-out seeds that advantage disappears entirely. Reporting it would have
shown a warm-start win that does not exist.
**Figure.** `figures/terrain_warm_s4.png`.
**Limitations.** Equal budget across unequal dimensions still applies; what the
warm start rules out is the specific objection that the S = 4 row never had
access to the S = 2 optimum. sep-CMA-ES is diagonal-only; the row stays †.

---

### §11 — Validating the gradient-steering mechanism
**Commit** `f73cc8a`.
**Question.** §§4 and 6 established *where* the terrain effect is and that a
scalar field does not produce it. Neither measured the proposed mechanism.
**The algebra, which decides what to regress.** With slope = 0 the residual is
exactly

```
residual = ω_actual − ω_commanded = v·(m_R − m_L)/ℓ + (ω/2)·(m_R + m_L − 2)
```

and to first order about the robot centre, with `n̂` from the left wheel contact
to the right,

```
residual = v·∂m/∂n  +  ω·(m(centre) − 1)
           ⌞gradient⌟   ⌞mean-traction⌟
```

Both terms are the **same** per-wheel mechanism. This is arithmetic verified to
six decimals against the simulator, not a second hypothesis. It matters because
the two terms are built from the same field and are therefore **correlated**, so
regressing on the gradient alone gives a **biased** slope, not merely a noisy
one. Both fits are reported. `∂m/∂n` is differenced from the field at the robot
**centre**, never from the two wheel samples — the wheel difference is what the
residual is made of, so regressing on it would be an identity.
**Design.** `configs/sweeps/terrain_mechanism_regression.toml`, θ_m = 0.9,
λ = 0.10 m, 100 runs/cell, **12 million robot-timesteps pooled per row**,
accumulated as OLS sufficient statistics that add across runs.
**Headline.**

| row | axle | **ℓ/λ** | R₀ | full slope | full R² | gradient-only slope | gradient-only R² |
|---|---|---|---|---|---|---|---|
| axle-half-R0-same ‡ | 2.55 cm | **0.25** | 14.45 cm | **0.976** | **0.9983** | 0.522 | 0.0215 |
| base | 5.10 cm | **0.51** | 14.45 cm | 0.900 | 0.9738 | 0.681 | 0.1367 |
| R0-half-axle-same ‡ | 5.10 cm | **0.51** | 7.22 cm | 0.894 | 0.9719 | 0.652 | 0.0924 |
| R0-x2-axle-same ‡ | 5.10 cm | **0.51** | 28.90 cm | 0.901 | 0.9760 | 0.809 | 0.2408 |
| axle-x2-R0-same ‡ | 10.20 cm | **1.02** | 14.45 cm | **0.623** | **0.7373** | 0.539 | 0.2776 |

Three results: (i) slope **0.976** with R² **0.998** at the narrowest axle — the
residual *is* the first-order per-wheel effect and there is essentially nothing
else in it; (ii) both fall monotonically with ℓ/λ, steepest past ℓ/λ = 1, exactly
where a first-order expansion about the centre stops describing what the wheels
see; (iii) **the control works** — three rows at ℓ/λ = 0.51 span a **4× range of
R₀** and agree to **0.007 in slope** and 0.004 in R².
**The distinction this forces.** R₀ sets *where the swarm-level terrain effect
peaks*; ℓ/λ sets *how well a first-order expansion describes one robot's turn
rate*. Different questions about different objects.
**The gradient-only column, as literally specified.** Slopes 0.52–0.81, R²
0.02–0.28 — nowhere near 1 at any ℓ/λ. That is the predicted consequence of
omitting a correlated term; at these constants the mean-traction term is roughly
**ten times** the gradient term, so it dominates both variance and bias.
Reported, and stopped there — no third mechanism.
**Figure.** `figures/terrain_mechanism_regression.png`
(`harness/figures_mechanism_regression.py`).
**Limitations.** One θ_m. The single-λ caveat is **discharged by §16**.

---

### §12 — Idea B Pareto front: what survival costs
**Commit** `91b8d57`; r_p normalisation at `c65abe2`.
**Question.** Every earlier Idea B figure scored survival alone, which cannot see
what surviving cost.
**Design.** `configs/sweeps/pursuer_pareto.toml`, five rows at h = 1.93 s,
ρ = 1.5, n = 20, τ = 120 s, R = 0.74 m, 100 runs/cell, three cells:
r_p = 0.2 m (0.27 R), 0.35 m (0.47 R), 1.0 m (**1.35 R — perfect perception**).
`final_dispersion` is already computed over *surviving* robots in the centroid
frame. The base-task axis is dropped below three survivors, because with one or
zero survivors the dispersion of "the survivors" is 0 — a perfect aggregation
score for a wiped-out swarm.
**Headline.**

| cell | row | survival at τ | dispersion (survivors ≥ 3) | runs kept | wiped out | median t_wipeout |
|---|---|---|---|---|---|---|
| **r_p = 0.2 m = 0.27 R, κ = 0** | B0-blind | 0.000 [0.000, 0.000] | 1.426 [1.363, 1.497] | 23 | 72% | 47.1 s |
| | B1-ternary ‡ | 0.475 [0.200, 0.750] | 1.630 [1.510, 1.787] | 68 | 12% | 81.0 s |
| | B2-ternary-side ‡ | 0.150 [0.100, 0.275] | 1.443 [1.417, 1.560] | 52 | 21% | 63.8 s |
| | B3-ternary-memory ‡ | 0.650 [0.400, 0.800] | 1.597 [1.538, 1.749] | 79 | 1% | 109.8 s |
| | **D-dispersive ‡** | **0.750 [0.675, 0.750]** | **379.9 [344.3, 399.9]** | 100 | 0% | — |
| **r_p = 0.35 m = 0.47 R, κ = 3** | B0-blind | 0.800 [0.750, 0.850] | 1.451 [1.412, 1.501] | 97 | 2% | 91.4 s |
| | B1-ternary ‡ | 0.800 [0.800, 0.850] | 1.508 [1.461, 1.573] | 98 | 2% | 106.5 s |
| | B2-ternary-side ‡ | 0.850 [0.800, 0.850] | 1.502 [1.445, 1.558] | 98 | 2% | 91.5 s |
| | B3-ternary-memory ‡ | 0.800 [0.800, 0.850] | 1.523 [1.484, 1.575] | 97 | 0% | — |
| | **D-dispersive ‡** | 0.650 [0.600, 0.700] | 386.3 [357.9, 431.3] | 100 | 0% | — |
| **r_p = 1.0 m = 1.35 R, κ = 3** (perfect perception) | B0-blind | 0.000 [0.000, 0.000] | not estimable (1/100) | 1 | 96% | 97.6 s |
| | B1-ternary ‡ | 0.000 [0.000, 0.000] | 10.3 [6.8, 15.1] | 12 | 66% | 107.9 s |
| | B2-ternary-side ‡ | 0.000 [0.000, 0.000] | not estimable (4/100) | 4 | 90% | 103.6 s |
| | B3-ternary-memory ‡ | 0.000 [0.000, 0.000] | not estimable (9/100) | 9 | 66% | 105.3 s |
| | **D-dispersive ‡** | **0.350 [0.325, 0.400]** | **504.8 [432.9, 613.9]** | 94 | 0% | — |

**Three readings.** (i) The cost is two orders of magnitude: D's dispersion is
**380–505** against **1.43–1.63** for every aggregating row. (ii) **At
r_p = 0.35 m = 0.47 R, κ = 3 there is no trade-off at all** — every aggregating
row beats D on *both* coordinates and D is Pareto-dominated. This is the regime
where confusion has made clustering safe *and* clustering is what the task wants.
(iii) At the other two cells the trade-off is real, but the r_p = 1.0 m cell is
the perfect-perception corner and says what happens when hiding is impossible,
not what happens at long range.
**Where survival saturates, timing still separates the rows.** At r_p = 0.2 m,
κ = 0: 47.1 s (B0), 63.8 s (B2), 81.0 s (B1), 109.8 s (B3) — the same ordering
the survival medians show at unsaturated cells.
**Changed.** Correction #12: report Idea B on two axes, not one.
**Figure.** `figures/pursuer_pareto.png` (`harness/figures_pareto.py`).
**Limitations.** Four of five rows hand-designed ‡; the front is between *spatial
strategies*, not capabilities. At the perfect-perception cell the base-task axis
is not estimable for three of four aggregating rows. One h, one ρ, one n, one τ,
one start radius — and because r_p only means anything against R, all three cells
move together if the swarm starts in a different disc.

---

### §13 — The 2 × 2 tuning control: how much of §9 was terrain?
**Commit** `9fa30a5`.
**Question.** §9 concluded "re-tuning solves it", and that conflated two things.
S2-rough was tuned against **this objective** — median final dispersion at
n = 20, τ = 600 s, R = 0.74 m, under this repository's normalisation and
collision model — while Gauci's constants were found for a different one. "Tuned
for this objective" and "tuned for terrain" were not separated.
**Design.** `configs/sweeps/terrain_tuning_control.toml`, λ = 0.10 m
(λ/R₀(gauci) = 0.69), θ_m swept 0 → 0.9 in eight steps. **S2-flat** is the
missing cell: same optimiser, same budget (600 × 12), **same training seed base
(900 000)**, differing from S2-rough only in the θ_m of its training condition.
**Pre-registered rule.** (a) S2-flat degrades like Gauci while S2-rough holds →
terrain moves the optimal parameters. (b) They overlap in CI at every θ_m →
terrain is a performance tax on a fixed controller. (c) They cross → a trade-off
exists; report the crossing and reopen the terrain bit.
**Branch fired: (c). They cross.** Paired by run index (both rows share a seed
base, so run *i* is the same placement and field in both):

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

Sign flip between θ_m = 0.30 and 0.45, significant on both sides.
**The decomposition, and the sentence it must always be quoted in.**
Decomposing the Gauci → S2-rough gap at θ_m = 0.9 gives **96.9%
objective-tuning and 3.1% terrain-tuning at start radius 0.74 m, against
99.7% / 0.3% at 1.5 m** (§14) — the two figures travel together, because the
terrain share is the part that does not survive a change of initial condition:

| row | dispersion at θ_m = 0.9 | share of the gap |
|---|---|---|
| S2-gauci | 3.150 | |
| S2-flat † | 1.438 | **96.9% — objective-tuning** (99.7% at 1.5 m) |
| S2-rough † | 1.383 | **3.1% — terrain-tuning** (0.3% at 1.5 m) |

On flat ground the terrain-tuning term *reverses*: S2-rough costs 4.1% against
S2-flat. So terrain-tuning is worth about ±4% of dispersion in either direction,
while tuning for this objective at all is worth 119%.
**Hold ratios at θ_m = 0.9**, each row against its own flat baseline: S2-gauci
**2.208 [1.904, 2.410]**, S2-flat **1.195 [1.146, 1.265]**, S2-rough **1.104
[1.078, 1.150]**. A controller that never saw terrain degrades by 20% where
Gauci's degrades by 121%.
**Changed.** §9's headline was right about the direction and wrong about the
cause. Two consequences: the H2 degradation curve is largely a property of
Gauci's specific constants — the published ~2.2× overstates what terrain does to
a well-matched controller by about a factor of six — and the terrain bit was
briefly reopened at the S2-flat ↔ S2-rough pair, then **closed again by §14**.
**Figure.** `figures/terrain_tuning_control.png`
(`harness/figures_tuning_control.py`); the crossing panel is repeated against
§14's 1.5 m re-run in `figures/terrain_decision_rule_regimes.png`
(`harness/figures_decision_rule_regimes.py`).
**Limitations.** One λ, one n, one start radius, one τ — **§14 answers this and
the answer is no**. Both searched rows are †. The crossing is located by a sign
flip on an eight-step grid with both bracketing CIs including zero.

---

### §14 — The searched rows' advantage is regime-specific
**Commit** `d0d95c3`.
**Question.** Does §9/§13's comparison survive outside the initial condition the
rows were searched in?
**Design.** `configs/sweeps/terrain_regime_robustness.toml` — S2-gauci, S2-flat †,
S2-rough † at θ_m ∈ {0, 0.9} × start radius ∈ {0.74, 1.5, 3.0} m × n ∈ {20, 50},
λ = 0.10 m, 100 runs/cell, 3 600 trials. Rows paired by run index within a cell.
Plus two companions: `terrain_tuning_control_r15.toml` (§13's grid re-run at
1.5 m, 2 400 trials) and `terrain_regime_tau.toml` / `..._tau_flat.toml` (the
3.0 m cell at τ = 600, 1800, 3600 s, all rows, both n).
**Headline — the advantage inverts with start radius.** Paired ratio of Gauci's
dispersion to the row's at θ_m = 0.9 (**> 1 means the row beats Gauci**):

| n | start radius | S2-flat † | S2-rough † |
|---|---|---|---|
| 20 | 0.74 m | **1.942 [1.645, 2.267]** | **2.129 [1.807, 2.446]** |
| 20 | 1.5 m | 1.541 [1.285, 1.647] | 1.475 [1.199, 1.729] |
| 20 | 3.0 m | **0.296 [0.170, 0.638]** | **0.137 [0.098, 0.210]** |
| 50 | 0.74 m | 1.181 [1.096, 1.235] | 1.191 [1.117, 1.282] |
| 50 | 1.5 m | 1.280 [1.158, 1.438] | 1.216 [1.099, 1.374] |
| 50 | 3.0 m | 0.902 [0.628, 1.094] | 0.807 [0.643, 0.944] |

At 3.0 m, n = 20, θ_m = 0.9: Gauci's median dispersion is 3.902, S2-flat's
19.512, S2-rough's **37.995**; reach is 0.46 [0.37, 0.56] against 0.23 and
**0.11**.
**At n = 50 both searched rows are worse than Gauci on flat ground at every
radius**: paired ratios 0.973 / 0.944 at 0.74 m, 0.870 / 0.818 at 1.5 m,
0.775 / 0.777 at 3.0 m, all with intervals below 1. Gauci holds 1.204–1.206 at
every radius while the searched rows drift 1.25 → 1.55.
**Hold ratios reverse too** (n = 20): at 0.74 m Gauci 2.149 [1.853, 2.455],
S2-flat 1.200 [1.124, 1.272], S2-rough 1.099 [1.044, 1.145] — reproducing §13; at
3.0 m Gauci **2.810 [2.187, 3.902]**, S2-flat **15.998 [11.326, 25.132]**,
S2-rough **28.540 [20.789, 35.070]**.
**Mechanism: they bought holding with gathering rate.** Median time to first
single cluster **on flat ground**, n = 20, among runs that reached one:

| start radius | S2-gauci | S2-flat † | S2-rough † |
|---|---|---|---|
| 0.74 m | 20 s [20, 20] | 30 s [20, 30] | 30 s [20, 30] |
| 1.5 m | 60 s [50, 60] | 90 s [80, 90] | 90 s [90, 100] |
| 3.0 m | 140 s [130, 150] | 280 s [260, 295] | **330 s [310, 345]** |

The search shrank the blind-state turning circle from 14.45 cm to about 5 cm. A
tight circle holds a cluster that already exists; it also covers ground slowly,
and **the blind state *is* the search behaviour**. At the tuned radius the cost is
invisible (30 s against 20 s inside a 600 s budget); at 3.0 m it is 2.0–2.4×.
**Failure or truncation? τ extended 6×.** At 3.0 m, θ_m = 0.9, n = 20:

| τ | S2-gauci reach / disp | S2-flat † | S2-rough † | ratio flat | ratio rough |
|---|---|---|---|---|---|
| 600 s | 0.46 / 3.902 | 0.23 / 19.512 | 0.11 / 37.995 | 0.296 [0.170, 0.638] | 0.137 [0.098, 0.210] |
| 1800 s | 0.99 / 2.927 | 0.53 / 2.054 | 0.29 / 26.275 | 0.996 [0.338, 1.333] | 0.141 [0.091, 0.245] |
| 3600 s | 1.00 / 2.888 | 0.60 / 1.907 | 0.34 / 24.006 | 1.297 [0.960, 1.495] | 0.148 [0.104, 0.300] |

**S2-flat's collapse was largely truncation** — given six times the budget it
draws level with Gauci, interval still containing 1, and nowhere near the 1.94 it
manages at the tuned radius. **S2-rough's is not**: the ratio does not move at
all (0.137, 0.141, 0.148) and two thirds of its runs never form a cluster inside
six times the budget that was enough for every Gauci run. At n = 50 the inversion
*was* truncation: every ratio crosses back above 1 as τ grows, to ~1.1.
**The n = 50 flat-ground deficit is not truncation**: at 3.0 m, θ_m = 0, six
times the budget moves it from 0.775 / 0.777 only to 0.839 [0.795, 0.880] /
0.805 [0.779, 0.835], while Gauci's own dispersion moves 1.204 → 1.209.
**§13's decision rule re-run at 1.5 m: branch (b), not (c).** S2-flat is
significantly better at θ_m ≤ 0.3 and there is **no θ_m at which S2-rough is
significantly better**; the cell that decided §13 (θ_m = 0.6, +0.0421 [+0.0107,
+0.0659] at 0.74 m) is null here at −0.0008 [−0.0134, +0.0433]. The decomposition
at 1.5 m is **99.7% objective-tuning and 0.3% terrain-tuning**. Hold ratios at
1.5 m: S2-gauci 2.053 [1.804, 2.383], S2-flat 1.302 [1.201, 1.592], S2-rough
1.231 [1.139, 1.470].
**Changed.** Correction #11 rewritten in full: re-tuning does not solve terrain,
it hides terrain behind a much larger objective mismatch, in one initial
condition. The terrain bit stays closed. A re-searched baseline is necessary but
not sufficient — it must also be shown to transfer.
**Figures.** `figures/terrain_regime_robustness.png`
(`harness/figures_regime_robustness.py`),
`figures/terrain_decision_rule_regimes.png`
(`harness/figures_decision_rule_regimes.py`).
**Limitations.** Two θ_m on the main grid; τ extended only in the 3.0 m cell;
start radius and n crossed but density confounded with both (n = 50 at 0.74 m is
2.5× the density of n = 20); dispersion compared within a cell only; both rows †.

---

### §15 — The worst correlation length does not follow the controller
**Commit** `628570b`.
**Question.** Every terrain sweep had run at λ = 10 cm, which is 0.69 R₀ for
Gauci and 2.11 R₀ for S2-rough. If H2's "worst at λ/R₀ ≈ 0.7" is a
controller-relative law, S2-rough's own worst λ is near 3.3 cm and §13's
comparison was on-peak for one row and off-peak for the other.
**Design.** `configs/sweeps/terrain_lambda_sweep.toml`, λ log-spaced 2 → 20 cm in
eight steps, θ_m ∈ {0, 0.9}, n = 20, τ = 600 s, R = 0.74 m, 100 runs/cell, 3 200
trials. Hold ratios paired by run index against the same run on flat ground.
**Pre-registered rule.** If S2-rough peaks near λ/R₀ ≈ 0.7, H2 is
controller-relative; if the peak is elsewhere or absent, report where it is and
**stop** — no third mechanism.
**Branch fired: the peak is elsewhere.**

| λ (cm) | λ/R₀ gauci | λ/R₀ rough | S2-gauci | S2-rough † |
|---|---|---|---|---|
| 2.00 | 0.14 | 0.42 | 1.390 [1.287, 1.462] | 1.047 [1.011, 1.071] |
| 2.78 | 0.19 | 0.59 | 1.482 [1.408, 1.617] | 1.052 [1.034, 1.077] |
| 3.86 | 0.27 | 0.81 | 1.788 [1.654, 1.995] | 1.091 [1.070, 1.114] |
| 5.37 | 0.37 | 1.13 | 2.155 [1.829, 2.622] | 1.082 [1.048, 1.112] |
| **7.46** | **0.52** | **1.57** | **2.505 [2.263, 2.822]** | **1.121 [1.090, 1.222]** |
| 10.36 | 0.72 | 2.19 | 2.082 [1.853, 2.510] | 1.086 [1.063, 1.166] |
| 14.39 | 1.00 | 3.04 | 1.664 [1.492, 2.052] | 1.064 [1.041, 1.151] |
| 20.00 | 1.38 | 4.22 | 1.519 [1.274, 1.714] | 1.012 [0.991, 1.083] |

**Both rows peak at the same λ in metres — 7.46 cm** — which is λ/R₀ = 0.52 for
Gauci and **1.57** for S2-rough. At S2-rough's predicted worst λ its hold ratio is
1.05–1.09, in the bottom half of its range, and the profile rises monotonically
from λ/R₀ = 0.42 to 1.57.
**Invariance check.** With θ_m = 0 the field is identically 1, so those cells must
not depend on λ: median dispersion is **identical to four decimals across all
eight λ** for both rows (1.4267 and 1.2530, spread 0). The ratios are therefore
terrain, not a baseline artefact.
**Reported and stopped, per the rule.** The shared peak sits within 1% of the
7.4 cm body diameter and at ℓ/λ = 0.68 for the 5.1 cm axle. Those are coincident
lengths this grid cannot separate, and **no mechanism was proposed**. S2-rough's
peak is weakly located — its CI at 7.46 cm overlaps those at 3.86, 5.37 and
10.36 cm — but the negative is settled: the peak is *not* at λ/R₀ ≈ 0.7.
**Changed.** §4's H2 survives as measured and loses its generalisation
(correction #13). §13's comparison was **not** off-peak: λ = 10 cm is one grid
step from the shared peak.
**Figure.** `figures/terrain_lambda_sweep.png`
(`harness/figures_lambda_sweep.py`). Its right panel scales each row's excess to
its own peak, because the two excesses differ twelvefold and on a shared absolute
axis the second curve is a flat line.
**Limitations.** One θ_m, one n, one start radius, one τ, two controllers. Eight
λ over one decade, so the peak is located to a grid step. λ = 2 cm is below the
3.7 cm body radius.

---

### §16 — The ℓ/λ collapse holds across λ
**Commit** `20d79b4`.
**Question.** §11 varied the axle at one λ, so "a function of ℓ/λ" and "a
function of ℓ" were the same claim.
**Design.** `configs/sweeps/terrain_lambda_collapse.toml`, θ_m = 0.9, λ ∈ {5, 10,
20} cm × axle ∈ {2.55, 5.10, 10.20} cm with constants adjusted to hold R₀ =
14.45 cm, 100 runs/cell, **12 million robot-timesteps pooled per point**. The
grid is built so the same ℓ/λ is reached by different (ℓ, λ) pairs: 0.51 three
ways, 0.255 and 1.02 two ways each.
**Headline.**

| ℓ/λ | axle | λ | full slope | full R² | gradient-only slope | gradient-only R² |
|---|---|---|---|---|---|---|
| 0.128 | 2.55 cm | 20 cm | **0.9943** | **0.9999** | −0.496 | 0.0046 |
| 0.255 | 2.55 cm | 10 cm | 0.9762 | 0.9983 | 0.522 | 0.0215 |
| 0.255 | 5.10 cm | 20 cm | 0.9760 | 0.9986 | 0.299 | 0.0059 |
| 0.510 | 2.55 cm | 5 cm | 0.8800 | 0.9667 | 0.807 | 0.1631 |
| 0.510 | 5.10 cm | 10 cm | 0.9001 | 0.9738 | 0.681 | 0.1367 |
| 0.510 | 10.20 cm | 20 cm | 0.8994 | 0.9749 | 0.610 | 0.0790 |
| 1.020 | 5.10 cm | 5 cm | 0.6068 | 0.7429 | 0.572 | 0.3830 |
| 1.020 | 10.20 cm | 10 cm | 0.6228 | 0.7373 | 0.539 | 0.2776 |
| 2.040 | 10.20 cm | 5 cm | **0.1351** | **0.0870** | 0.131 | 0.0633 |

Spread at matched ℓ/λ: **0.0001** in slope at 0.255 (2 points, λ = 10 and 20 cm),
**0.0201** at 0.510 (3 points, λ = 5, 10, 20 cm), **0.0160** at 1.020 (2 points).
**Max slope spread at matched ℓ/λ: 0.0201**, and the same excluding the widest
axle — the outlier at 0.51 is the *narrowest* axle at the *smallest* λ, not the
caveated wide one. That is **2.3%** of the 0.86 range the trend covers.
**Two things the added λ buy.** A cleaner top end: ℓ/λ = 0.128 gives slope
**0.9943**, R² **0.9999**. And a bottom end where the expansion fails outright:
ℓ/λ = 2.04 gives slope 0.135, R² 0.087 — past ℓ/λ ≈ 1 the linearisation stops
explaining the residual rather than merely degrading. Monotone: 0.994 → 0.976 →
0.89 → 0.61 → 0.135.
**Changed.** §11's single-λ limitation discharged; correction #14 records the
established range (4× in λ, 4× in axle, one decade of ℓ/λ, at θ_m = 0.9).
**Figure.** `figures/terrain_lambda_collapse.png`
(`harness/figures_lambda_collapse.py`).
**Limitations.** One θ_m, one n, one τ, one start radius. Four of nine points come
from ‡ rows. `axle-x2` puts wheel contacts outside the body and carries the
ℓ/λ = 2.04 point and one of the two at 1.02, so the *shape* past ℓ/λ = 1 rests on
it. Three λ over a 4× range; nothing licenses λ = 1 cm or λ = 1 m.

---

### §17 — Doubling R₀ does not double the worst λ
**Commit** `9335c56`.
**Question.** §15 compared two controllers differing in every constant, so "the
peak is at a fixed λ" could still be a fact about one searched row. Test it inside
one family where R₀ is the only thing that moves.
**Design.** Three rows of Gauci's table differing **only in the state-0 forward
constant**: R0-half-axle-same ‡ (R₀ 7.23 cm), base (14.45 cm), R0-x2-axle-same ‡
(28.89 cm). λ log-spaced 2 → 38.6 cm in ten steps (§15's eight-point grid
continued at the same ratio so the largest row's predicted peak is interior),
θ_m ∈ {0, 0.9}, n = 20, τ = 600 s, 100 runs/cell, 6 000 trials **per start
radius**. Two start radii: 1.5 m as specified (`terrain_lambda_r0_family.toml`)
and 0.74 m as a companion (`..._r074.toml`). Ratio-law predictions use 0.52 R₀,
the base row's *measured* peak ratio from §15: 3.76, 7.51, 15.02 cm.
**The validity window, and why the companion exists.** A hold ratio means "how
much looser is the cluster" only while there *is* a cluster. At 1.5 m, λ ≥ 20 cm
drives every row's reach to 0.4–0.5, and the base row's apparent maximum there is
**5.112 at λ = 38.6 cm with reach 0.41** — a peak in failure. So: **a peak is read
only where reach at θ_m = 0.9 is at least 0.8.** That threshold was fixed *after*
seeing the 1.5 m sweep, so its use there is post hoc and is labelled; the 0.74 m
companion was run afterwards with it fixed in advance, and the decision rule is
read from that sweep.
**Pre-registered rule.** (a) Peaks near 3.7, 7.5, 15 cm → the ratio law survives.
(b) All three peaks within CI of ~7.5 cm → the λ/R₀ law is dead. (c) Mixed →
report which rows fall where and stop.
**Branch fired: (b), on the two rows that can be measured.**

| row | R₀ | λ inside window | peak λ | 95% CI | λ/R₀ at peak | ratio-law prediction |
|---|---|---|---|---|---|---|
| R0-half-axle-same ‡ | 7.23 cm | 10/10 | **5.37 cm** | [3.86, 10.36] | 0.74 | 3.76 cm |
| base | 14.45 cm | 10/10 | **7.46 cm** | [5.37, 7.46] | 0.52 | 7.51 cm |
| R0-x2-axle-same ‡ | 28.89 cm | **0/10** | — | — | — | 15.02 cm |

**Peak ratio, base ÷ R0-half: 1.39 [0.72, 1.93]** — an interval that **excludes
the ratio law's 2.00 and contains a fixed scale's 1.00**. Computed by resampling
the run-index axis the three rows share and recomputing both peaks per replicate,
so it is a paired interval on the ratio.
**The third row cannot be measured, and that is informative.** Its reach at
θ_m = 0.9 never exceeds 0.73, and on *flat* ground its median dispersion is 2.902
against 1.427 (base) and 1.264 (R0-half): a 28.9 cm turning circle is 39% of the
0.74 m start radius. Its unrestricted argmax is 10.36 cm — nowhere near its
15.02 cm prediction — but it is excluded rather than used as corroboration.
**On the λ/R₀ axis the peaks sit at 0.74, 0.52 and 0.36** — spread by almost
exactly the R₀ ratios, which is what a fixed λ looks like divided by a moving R₀.
Under the ratio law that panel is where the curves should coincide.
**The 1.5 m sweep, reported as a result about the metric.** Restricted peaks:
R0-half 10.36 cm [5.37, 10.36] on 6/10 usable λ; base 5.37 cm [3.86, 5.37] on
4/10; R0-x2 none. Peak ratio **0.52 [0.37, 1.00]** — the ordering *reverses*. The
supportable reading is that the restricted windows are too small and too different
between rows for the comparison to mean anything.
**Changed.** §15's H2 statement rewritten; correction #13 gains the within-family
evidence. Experiment §18 follows because the fixed-scale branch fired.
**Figure.** `figures/terrain_lambda_r0_family.png`
(`harness/figures_lambda_r0_family.py`).
**Limitations.** One θ_m, one n, one τ, two start radii, one controller family.
Two ‡ rows. One of three rows produced no measurement, so "all three peaks
coincide" was never testable. **"Fixed" is consistent; "sub-proportional" is not
excluded** — the point estimate 1.39 lies between 1.00 and 2.00. Peaks are
located to a log grid of ratio 1.39, which is also the size of the effect.

---

### §18 — The worst λ is the body diameter
**Commit** `5b72abc`.
**Question.** §15 noticed the shared peak sits within 1% of the 7.4 cm body
diameter; body diameter is the one length neither §15 nor §17 varied.
**Design.** `configs/sweeps/terrain_lambda_body.toml`, body diameter ∈ {3.7, 7.4,
14.8} cm with **R₀ (14.45 cm), the axle (5.1 cm), the sensor model and the start
radius (0.74 m) held**, λ 2 → 38.6 cm, θ_m ∈ {0, 0.9}, n = 20, τ = 600 s, 100
runs/cell, 6 000 trials. The validity window is §17's, **fixed before this sweep
ran**.
**The statistic has to be the hold ratio.** Dispersion is normalised by robot
radius squared and the cluster link distance is three body radii, so absolute
dispersion is not comparable across body sizes; a ratio of two dispersions at the
*same* body size cancels both exactly.
**Pre-registered rule.** If peak λ tracks body diameter (log-log slope near 1,
CI excluding 0), record the length scale **as** the body diameter and propose no
mechanism. If not, record 7.46 cm as a fixed scale of unknown origin.
**Branch fired: it tracks.**

| row | body diameter | λ inside window | peak λ | 95% CI | peak / diameter |
|---|---|---|---|---|---|
| body-half ‡ | 3.7 cm | **0/10** | — | — | — |
| body-base | 7.4 cm | 10/10 | **7.46 cm** | [5.37, 7.46] | **1.01** |
| body-x2 ‡ | 14.8 cm | 10/10 | **14.39 cm** | [10.36, 20.00] | **0.97** |

**Log-log slope of peak λ on body diameter: 0.948 [0.474, 1.897]** — excludes 0,
contains 1. `body-x2` is the cleanest curve in the document: reach 1.00 at every
λ but the last, where it is 0.99.
**The sensitivity, stated because it decides how much the headline is worth.**
`body-half` reaches a cluster in at most 72% of runs at any λ and its flat-ground
dispersion is **3.057 against 1.427** — a 3.7 cm robot in a 0.74 m start disc,
twenty body diameters across, does not aggregate at this radius at all. It also
**does not support the relation**: its unrestricted argmax is 7.46 cm = **2.02
body diameters**. Including it drops the log-log slope from 0.948 to **0.474**.

| rows used | slope | reading |
|---|---|---|
| the two inside the window | **0.948 [0.474, 1.897]** | the peak *is* the body diameter |
| all three, ignoring the window | 0.474 | the peak moves with the body, sub-proportionally |

Both exclude 0, so "the body is irrelevant" is rejected either way; the difference
between "is the diameter" and "moves with it" rests entirely on excluding a row
that is not performing the task.
**Three lengths scale with the body and this sweep separates none**: the body
diameter itself as the size of an obstacle; the **cluster link distance**, three
body radii = 1.5 body diameters, which is the *metric's* own definition of
"together"; and the **occlusion footprint**, since a larger body blocks more
line-of-sight. Two further quantities move with it and cannot be held at the same
time as the start radius: the **packing fraction** at n = 20 in a 0.74 m disc,
which is 0.0125, 0.05 and 0.20 across the three rows; and at 3.7 cm the 5.1 cm
axle puts the wheel contacts outside the body.
**Changed.** Correction #13 gains its answer: the worst correlation length is the
size of the robot, not a property of its controller. No mechanism proposed.
**Figure.** `figures/terrain_lambda_body.png` (`harness/figures_lambda_body.py`).
**Limitations.** Two usable body sizes; a two-point log-log slope has a wide
interval. One θ_m, one n, one τ, one start radius, one controller, one arena.
Peaks located to a log grid of ratio 1.39, so "1.01 body diameters" means "the
same grid step as the body diameter".

---

### §19 — A transferring four-constant controller exists, and it is the baseline
**Commit** `e6c4145`.
**Question.** §14 showed two single-condition searched rows failing to transfer.
That is a statement about two controllers, not about the capability: nothing had
asked the optimiser to work anywhere but the arena it was given.
**Design.** Two class searches (`configs/search/train_s2_class_flat.toml` and
`..._rough.toml`): sep-CMA-ES, **1200 × 12 — double §9's budget**, six-condition
class `radius ∈ {0.74, 1.5, 3.0} m × n ∈ {20, 50}`, objective the geometric mean
of per-condition medians, training seed bases 910 000 and 920 000. Evaluated by
`configs/sweeps/terrain_class_eval.toml` on §14's full grid (12 cells × 5 rows,
6 000 trials) plus `..._eval_tau.toml` (the 3.0 m cells at τ = 600, 1800, 3600 s).
**Pre-registered rule.** (1) A class row matches or beats Gauci at every cell → a
transferring controller exists. (2) Wins in some cells and loses in others →
report the cells and the R₀ trade, and say whether §14's gather/hold reading
predicts the pattern. (3) Loses everywhere → Gauci is dominant; make it a
correction.
**Branch fired: (2).** Cell counts on §14's grid at τ = 600 s (paired ratio
Gauci ÷ row; W = interval entirely above 1, L = entirely below):

| row | W | L | tied |
|---|---|---|---|
| S2-flat † | 7 | 4 | 1 |
| S2-rough † | 7 | 5 | 0 |
| **S2-class-flat †** | **9** | **2** | **1** |
| S2-class-rough † | 7 | 5 | 0 |

**The class objective fixed the swarm-size failure completely.** On flat ground at
n = 50 the single-condition rows lose everywhere — 0.973, 0.870, 0.775 (S2-flat)
and 0.944, 0.818, 0.777 (S2-rough), all with intervals below 1, and §14 showed
six times the trial length does not close it. S2-class-flat scores **1.026 [1.020,
1.033], 1.016 [1.009, 1.023], 0.999 [0.991, 1.008]**: two wins and a tie. Its
absolute dispersion at n = 50, 3.0 m is **1.200** against Gauci's 1.204, where
S2-flat sits at 1.545.
**Both losses are at 3.0 m under terrain**, and that column needs a longer trial
for **every** row — at τ = 600 s Gauci itself reaches in only **46%** of runs
there. At τ = 3600 s, n = 20:

| row | reach | dispersion | paired ratio |
|---|---|---|---|
| S2-gauci | 1.00 [0.96, 1.00] | 2.888 | — |
| **S2-class-flat †** | 0.86 [0.78, 0.91] | **1.76** | **1.436 [1.249, 1.673]** |
| S2-flat † | 0.60 [0.50, 0.69] | 1.907 | 1.297 [0.960, 1.495] |
| S2-rough † | 0.34 [0.25, 0.44] | 24.006 | 0.148 [0.104, 0.300] |
| S2-class-rough † | 0.36 [0.27, 0.46] | 13.42 | 0.269 [0.148, 0.643] |

At n = 50, 3.0 m, τ = 3600 s S2-class-flat ties: 1.063 [0.934, 1.172], reach 0.95
against 1.00. **So with the 3.0 m column at the trial length Gauci needs there
too, S2-class-flat is 10 W, 2 tied, 0 L on dispersion across the twelve cells.**
**Reach is where Gauci still wins, and it is why the exception exists.** At
θ_m = 0.9, with the 3.0 m cells at τ = 3600 s: S2-class-flat is better at
r₀ = 0.74 m (0.98 [0.93, 0.99] against 0.86 [0.78, 0.91]), tied at 1.5 m and at
n = 50 / 0.74 m and 1.5 m, and **worse at both 3.0 m cells** (0.86 against 1.00 at
n = 20; 0.95 against 1.00 at n = 50). On flat ground every row reaches in every
run at every radius.
**The R₀ trade, and §14's reading predicting the pattern.** Training on the class
at θ_m = 0 moved R₀ from S2-flat's 5.53 cm to **7.47 cm** — 35% of the way back to
Gauci's 14.45 cm; training on the class at θ_m = 0.9 moved it 4.74 → 4.47 cm,
i.e. not at all. Flat-ground time to first cluster at 3.0 m, n = 20, is **monotone
in R₀ across all five rows**: Gauci **140 s** (R₀ 14.45), S2-class-flat **245 s**
(7.47), S2-flat **280 s** (5.53), S2-rough **330 s** (4.74), S2-class-rough
**340 s** (4.47). Every loss in the section is at 3.0 m under terrain, where reach
binds, and nowhere else.
**Changed.** The c*(θ) baseline moved from Gauci to **S2-class-flat †**, with
Gauci kept as the enumerated reference and as the row that owns the 3.0 m terrain
corner. **Correction #15**: search the mission class, not one arena.
**Figure.** `figures/terrain_class_search.png`
(`harness/figures_class_search.py`).
**Limitations recorded at the time.** Two class searches, **one optimiser seed
each** — §21 addresses this. The class is six points on two axes; λ, θ_m, τ and
the arena are fixed, so "transfers" means "transfers across start radius and swarm
size". S2-class-rough's training objective was truncated at the conditions it most
needed to improve (**this diagnosis was wrong — see §20**). Both class rows are †.
The doubled budget removes the direction of the confound with §9 but not its
magnitude: 1200 evaluations over six conditions is 200 per condition against §9's
600.

---

### §20 — The τ-corrected class search: §19's diagnosis was wrong
**Commit** `3229c59` (machinery at `549ee04`).
**Question.** §19 attributed its rough-trained class row's unmoved R₀ to a
truncated training objective. Test it directly.
**Design.** `configs/search/train_s2_class_rough_tau.toml` — the same search with
**τ = 3600 s at the two 3.0 m conditions** and 600 s at the other four, given as
six explicit `--class-point` conditions because the class is not a product.
Everything else held: budget 1200 × 12, optimiser seed 1, and **the same training
seed base, 920 000**, so trial length is the only difference. Evaluated by
`configs/sweeps/terrain_class_tau_eval.toml` (4 rows × 12 cells, 4 800 trials)
and `..._tau.toml` (2 400 trials).
**Headline: it changed nothing.** R₀ moved **4.47 → 4.44 cm**. Cell counts:
6 W / 5 L / 1 tied against S2-class-rough's 7 / 5 / 0. What moved was the
**state-1** response (L2 0.408 between the two rows), which is not where the
gathering-rate trade lives. At the cell the change targeted, τ = 3600 s, n = 20,
3.0 m: reach **0.26 [0.18, 0.35]** against S2-class-rough's 0.36 and Gauci's 1.00
— training *at* that trial length made it **worse** at that condition.
**The diagnostic that separates the two remaining explanations.**
`configs/sweeps/terrain_class_objective_probe*.toml` score four controllers on the
rough class's **own objective**, on its **own training seeds** (920 000), at 100
runs per condition instead of 2:

| row | 0.74/20 | 0.74/50 | 1.5/20 | 1.5/50 | 3.0/20 | 3.0/50 | **objective** |
|---|---|---|---|---|---|---|---|
| S2-gauci | 2.613 | 1.866 | 2.588 | 1.929 | 2.798 | 1.776 | 2.2237 |
| **S2-class-flat †** | 1.655 | 1.605 | 1.715 | 1.710 | 1.641 | 1.553 | **1.6456** |
| S2-class-rough † | 1.423 | 1.443 | 1.579 | 1.751 | 14.902 | 1.968 | 2.3456 |
| S2-class-rough-tau † | 1.416 | 1.346 | 1.573 | 1.656 | **36.762** | 1.921 | 2.6553 |

**S2-class-flat is a strictly better point on the objective this search was
minimising** — 1.6456 against the returned row's 2.6553 — and it was found by a
different search. The objective does not prefer a small R₀; the search failed to
find its own optimum.
**Why: the noise floor.** At 3.0 m, n = 20, τ = 3600 s the returned row's
dispersion runs from **1.14 to 242.50** over 100 runs, quartiles 13.69 and 73.59.
The search saw the median of **two** of those per evaluation:

| quantity | log units |
|---|---|
| 5th–95th percentile of the 2-run estimate at that cell (6.98 → 114.07) | **2.79** |
| the whole gap between the returned row and the better one that existed | **0.48** |

Noise **5.8×** the signal. A best-so-far selection under that noise returns
whichever candidate drew a lucky pair, which is why the search's own reported best
objective — **1.6009** — sits *below* the honest 100-run re-score of the same
constants, **2.6553**. Raising τ made it worse: it moved the hard cells from
"everything fails, uniformly" to "outcomes span two orders of magnitude", which is
more gradient *and* far more variance, and the variance won.
**What it does not undermine.** §19's baseline stands: S2-class-flat's status
rests on **held-out evaluation**, which is exactly what caught this. The one
number corrupted here is a training objective, and no claim rests on one.
**Changed.** Correction #15's third reporting requirement rewritten from "was the
training objective truncated" to "**is any one condition's per-evaluation estimate
noisier than the differences the search must resolve**", with the remedy being
runs per condition or a variance-stabilising statistic, not a longer trial.
**Figure.** `figures/terrain_class_tau.png` (`harness/figures_class_tau.py`).
**Limitations.** One optimiser seed. The probe shows a better point exists; it
does not locate the objective's optimum, so "the objective prefers a large R₀" is
not established either. The noise figure is for one condition at one θ_m. Both
class rows †.

---

### §21 — Phase 0: the baseline scatters across optimiser seeds
**Commit** `ce427a8`. **This is the freeze commit for Paper 1's experimental
record**; the freeze is declared at `2b736de`.
**Question.** S2-class-flat is the c*(θ) baseline and was found by **one**
optimiser seed. `docs/statistics.md` asks for two independent optimisers, or
failing that independent runs of one, with their agreement reported.
**Design.** The seed-1 search repeated with optimiser seeds 2 and 3 under the
identical protocol: sep-CMA-ES, 1200 × 12, the six-condition class
`radius ∈ {0.74, 1.5, 3.0} m × n ∈ {20, 50}`, θ_m = 0, geometric mean of
per-condition medians, and **the same training seed base, 910 000**. Only the
optimiser seed differs. Evaluated by `configs/sweeps/phase0_seeds.toml` (§14's
full held-out grid, 48 cells, 4 800 trials), `phase0_seeds_tau.toml` (the 3.0 m
θ_m = 0.9 column at τ = 600, 1800, 3600 s, 2 400 trials) and
`phase0_seeds_objective_probe.toml` (the honest re-score at 100 runs/condition on
the training seeds, 2 400 trials).
**Pre-registered rule.** (a) All three within CI of each other on every held-out
cell **and** R₀ within 10% → a reproduced optimum; item 12 closes; seed 1 stays
the baseline unless another seed dominates it. (b) They scatter → the baseline
becomes **best-of-three † per cell**, the scatter is the baseline's uncertainty,
and every downstream `c*(θ)` number is stated against best-of-three.
**Branch fired: (b). They scatter.**

| row | state-0 constants | R₀ | state-1 constants | reported objective | honest re-score | gap |
|---|---|---|---|---|---|---|
| S2-gauci | (−0.7000, −1.0000) | 14.45 cm | (+1.0000, −1.0000) | — | 1.2905 | — |
| S2-class-flat-s1 † | (−0.4330, −0.8820) | **7.47 cm** | (+0.7924, −0.8865) | 1.2143 | 1.2338 | +0.0194 |
| S2-class-flat-s2 † | (−0.5426, −0.9800) | **8.88 cm** | (+0.9467, −0.8113) | **1.1927** | **1.2246** | +0.0318 |
| S2-class-flat-s3 † | (−0.4097, −0.7527) | **8.64 cm** | (+0.7326, −0.6060) | 1.2120 | 1.2301 | +0.0181 |

**R₀ spread: 1.41 cm = 16.9% of the mean — outside the 10% rule.** All three moved
R₀ up from S2-flat's 5.53 cm toward Gauci's 14.45 cm (by 35%, 60%, 56% of the
way), so the *direction* of the gather-versus-hold trade reproduces in every seed
and the *magnitude* does not. L2 distances: seed1↔seed2 0.226, seed1↔seed3 0.315,
seed2↔seed3 **0.397** — larger than seed2↔Gauci at **0.252**.
**Held-out agreement: 4 of 12 cells contain a disjoint pair.** Three are the
n = 50 flat-ground cells (dispersion 1.171/1.163/1.162 at 0.74 m,
1.180/1.163/1.181 at 1.5 m, 1.200/1.166/1.191 at 3.0 m — differences of 0.02–0.03,
resolvable at 100 runs and practically small). The fourth is 3.0 m under terrain
at n = 20, τ = 600 s: dispersion **12.517 / 3.701 / 13.701**, reach 0.17 / 0.45 /
0.28 against Gauci's 0.46.
**That fourth cell is truncation.** At τ = 3600 s the three agree to **0.011** in
the paired ratio — **1.436 [1.249, 1.673], 1.430 [1.311, 1.746], 1.441 [1.224,
1.753]** — and all three beat Gauci; reach is 0.86 / 0.93 / 0.88 against Gauci's
1.00. At n = 50 and τ = 3600 s, seeds 2 and 3 win (1.088 [1.025, 1.213] and
1.120 [1.073, 1.213]) while seed 1 ties (1.063 [0.934, 1.172]).
**Cell counts against the enumerated reference at τ = 600 s:** seed 1 **9 W / 2 L
/ 1 tied**, seed 2 **10 W / 0 L / 2 tied**, seed 3 **10 W / 1 L / 1 tied**. **Seed
1 — §19's named baseline — is the weakest.** Head to head, paired by run index:
seed 2 beats seed 1 in 5 cells and loses in 2; seed 3 and seed 1 differ in 2 cells;
seed 2 beats seed 3 in 3 and loses in 2. **No seed dominates another**, so the
rule's "unless another dominates it" clause does not apply.
**The winner's-curse gap, measured for every seed: +0.019, +0.032, +0.018** — 1.5%
to 2.7%, an order of magnitude smaller than §20's **+1.05** for the rough class
(1.6009 reported against 2.6553 honest). That is the noise-floor account
predicting its own boundary: on flat ground every condition reaches a cluster in
every run and a 2-run median is a usable estimate; at θ_m = 0.9 it is not. The
*ordering* of the reported objectives also survives the re-score (seed 2 best on
both), so on flat ground the training objective ranks the seeds correctly even
while misstating their level.
**Changed.** The baseline is now **best-of-three † per cell** rather than a named
row. §19's substance is strengthened — three independent searches, every one
beating the enumerated reference in at least 9 of 12 cells, all three fixing the
n = 50 flat-ground failure that defeated every single-condition row — and its
naming of a single baseline row does not survive. Next-list item 12 closes with
"no: a reproduced *region*, not a reproduced optimum".
**Figure.** `figures/phase0_seed_reproducibility.png`
(`harness/figures_seed_reproducibility.py`).
**Limitations.** Three seeds reject "reproduced optimum" and do not characterise
the distribution: the spread is a range over three draws, not an interval on the
optimiser's variability. Two of the four disjoint cells differ by 0.02–0.03 —
statistically disjoint at 100 runs, practically small, and both facts are
reported. The scatter in the truncated cell is a τ artefact and is given at both
trial lengths. **Still one optimiser**: three seeds of sep-CMA-ES share its
diagonal covariance, so a bias common to that family would not show up. All three
rows remain †.

---

## 6. Results synthesis, by paper section

Each claim below carries a one-sentence statement, a grade, and the sections that
support it. Grades are defined in §7 and must not be upgraded when the paper is
written.

### A. Terrain (passive hostility)

**A1. The capability minimum does not move along the terrain dial.**
`c = (2, 0, 0, 0)` suffices at every θ_m from 0 to 0.9 at λ/R₀(gauci) = 0.69, at
start radius 0.74 m and at 1.5 m. Adding a fifth sensor state (the terrain bit)
does not help: at the peak cell the S = 4 row sits at 1.22 [1.16, 1.26] against
the searched S = 2 row's 1.10 [1.08, 1.15], **disjoint**; warm-starting the S = 4
search at the S = 2 optimum ties it (1.412 [1.349, 1.503] against 1.383 [1.350,
1.441], overlapping, point estimate 2.1% worse); and a hand-built composite that
switches between the two is worse than either at every θ_m (1.999 against 1.383
at θ_m = 0.9). *Grade: SUPPORTED (with the standing upper-bound caveat: no S = 4
controller better than the searched S = 2 one was found at equal budget).*
*Sections: §7, §9, §10, §23.*

> **The grade splits by swarm size, after experiment 2 (§23).** Stated as agreed:
>
> > At n = 20, no S = 4 row was found better than the searched S = 2 row at equal
> > budget (SUPPORTED †). At n ∈ {10, 50}, the n = 20-searched S = 4 rows are not
> > disjointly better than the best S = 2 row (SUGGESTED †: candidates
> > transferred, not searched at those n; margin 0.0069 at n = 10).
>
> Two reasons, and the second is not optional. **The margin**: disjointly worse at
> n = 20, overlapping at 50, overlapping by **0.0069 in hold-ratio units** at 10.
> n = 10 must not be written up as a clean hold. **The candidates**: the S = 4
> rows were *searched at n = 20 and transferred*, so at n ≠ 20 this tests whether
> n = 20-searched terrain-bit rows help elsewhere, not whether any S = 4 row at
> those n would. **The upper bound at n = 10 is only the transferred row.**
>
> The pre-registered τ contingency fired at n = 10 on the enumerated row alone —
> S2-gauci reaching a cluster in 0.71 of runs at τ = 600 s, every other row at
> 0.99–1.00 — and the whole block re-ran at τ = 3600 s, where its reach is 1.00.
> **That is the rule working**, and it is reported as such rather than as a hitch.
>
> Across the pseudo-reality family the claim as worded holds in the reference and
> in **9 of 10** perturbed models; in one — **model 09** — the terrain-bit row is
> disjointly *better*, at −0.055 [−0.088, −0.018], with no single-parameter cause
> (§25). One reversal in an upper-bound claim is a disclosure, not a refutation,
> and model 09 is named in §9.

**A2. Terrain is a performance tax on a fixed controller, and the size of the tax
depends almost entirely on how well matched the controller is.** At λ/R₀(gauci) =
0.69, θ_m = 0.9, hold ratios are S2-gauci **2.208 [1.904, 2.410]**, S2-flat
**1.195 [1.146, 1.265]**, S2-rough **1.104 [1.078, 1.150]**. A controller that
never saw terrain degrades by 20% where the published constants degrade by 121%,
so the published figure overstates what terrain does to a well-matched controller
by about a factor of six. *Grade: SUPPORTED. Sections: §13, §7, §9, §24.*

> **The matched-controller cost is a range over correlation length, not a single
> figure, after experiment 3 (§24).** Measured at λ = 0.05, 0.10 and 0.20 m under
> §12.1 D1's paired definition, the cost at θ_m = 0.9 is **+1.2 % to +21.4 %**
> across the three λ and both tuned rows — wider than the 10–20 % this claim
> quoted from λ = 0.10 m alone, and it must be written as a range over λ and said
> to be one. The driver is λ = 0.20 m, where S2-rough's hold ratio is
> **1.0116 [0.9911, 1.0826]** — an interval containing 1, so at that correlation
> length terrain costs a terrain-tuned controller nothing measurable.
>
> **One wrinkle that is not a λ effect.** The 10–20 % above comes from §13's
> *retired* ratio-of-medians hold ratios (1.195, 1.104). The range is computed
> under the paired form §12.1 D1 settled on, which on the very same 100 runs gives
> 1.2004 and 1.0988 → 20.0 % and 9.9 %. The λ = 0.10 m column therefore does not
> match this claim's original digits, and the difference is the change of
> statistic, not the correlation length.

**A3. Almost none of the re-tuned controller's advantage is terrain adaptation —
the terrain share is small at every correlation length measured, and it is not
zero.** Decomposing the Gauci → S2-rough gap at θ_m = 0.9: **96.9% objective-tuning
and 3.1% terrain-tuning at start radius 0.74 m, against 99.7% / 0.3% at 1.5 m**.
On flat ground the terrain-tuning term reverses and costs 4.1%. At three
correlation lengths the objective share is **95.0 / 96.9 / 94.4 %** (λ = 0.05 /
0.10 / 0.20 m), so the claim is better supported by three λ than it ever was by
one. *Grade: SUPPORTED †. Sections: §13, §14, §24. The 0.3% figure must appear in
the same sentence as the 3.1% one.*

> **"Small" and "zero" are different claims and only the first one holds.**
> Experiment 3 pre-registered a null test — does the paired terrain-tuning term at
> θ_m = 0.9 include zero? — and it **fails at two of the three λ, both above
> zero**: +0.0951 [+0.0456, +0.1366] at 0.05 m and +0.0368 [+0.0165, +0.0667] at
> 0.20 m, against +0.0818 [−0.0008, +0.1331] at 0.10 m. The direction narrows this
> claim rather than overturning it: terrain-tuning buys something real, and what
> it buys is 3–6 % of the gap.
>
> **λ = 0.10 m is not where the effect is smallest — it is where the interval is
> widest.** Its point estimate is more than twice λ = 0.20 m's, which fails; the
> interval widths are 0.1339 against 0.0502, and the hold is **by 0.0008**. Two
> seed-free checks on how thin that is: over 200 bootstrap seeds the λ = 0.10 m
> lower bound clears zero for 7 of 200 (200 of 200 at the other two λ), and a sign
> test on the 100 paired runs gives **59/100** there — not distinguishable from a
> coin flip — against 68/100 and 67/100, both disjoint from one. A null from a
> single correlation length was never strong evidence for a null.
>
> **The †, and why it is there.** Both tuned rows were trained at λ = 0.10 m, so
> the 0.05 and 0.20 m columns measure the *transfer* of a λ = 0.10-tuned
> controller and not the decomposition a λ-matched controller would show. A term
> that grows away from the training λ is consistent with "the term is real
> everywhere" and with "part of it is a mismatch penalty", and this design cannot
> separate them. Answering that needs a search at each λ.

**A4. The mechanism is per-wheel traction changing curvature, not speed
heterogeneity between robots.** A paired control that differs only in how the
field is sampled shows the scalar-centre row flat within [0.96, 1.01] across the
whole grid with no peak at all, pooled **0.980 [0.976, 0.986]**, against the
per-wheel row's peak of **2.21 [1.90, 2.41]** at λ/R₀ = 0.69 and pooled **1.175
[1.154, 1.190]**. *Grade: SUPPORTED (pre-registered rule, branch fired).
Section: §6.*

**A5. The mechanism lemma: the heading-rate residual is the first-order per-wheel
traction effect, and the quality of that linearisation is set by ℓ/λ.** The exact
decomposition is `residual = v·∂m/∂n + ω·(m(centre) − 1)`, both terms from the
same mechanism, verified to six decimals. Regressed over 12 million robot-timesteps
per point: slope **0.9943**, R² **0.9999** at ℓ/λ = 0.128, falling monotonically
to 0.9762 (0.255), 0.90 (0.51), 0.62 (1.02) and **0.1351**, R² **0.0870** at 2.04.
At matched ℓ/λ across a 4× range of λ the slope agrees to **0.0201** — 2.3% of the
0.86 range the trend covers — and to 0.0001 at ℓ/λ = 0.255. Regressing on the
gradient term alone gives slopes 0.52–0.81 and R² 0.02–0.28, which is the
predicted consequence of omitting a correlated term roughly ten times its size.
*Grade: SUPPORTED. Sections: §11, §16.*

**A6. There is a worst correlation length, it is about 7.5 cm in this arena, and
it is not proportional to R₀.** Two controllers differing threefold in R₀ peak at
the same λ, 7.46 cm (λ/R₀ = 0.52 and 1.57). Inside one controller family, doubling
R₀ moves the peak by **1.39× [0.72, 1.93]** — excluding the ratio law's 2.00,
containing a fixed scale's 1.00. *Grade: SUPPORTED for the rejection of
proportionality; SUGGESTED for "fixed", since the point estimate lies between 1
and 2 and a sub-proportional dependence is not excluded. Sections: §15, §17.
Supersedes §4's generalisation, which stands as measured.*

**A7. The worst λ tracks the body diameter.** With R₀, axle, sensor model and
start radius held, a 7.4 cm body peaks at 7.46 cm and a 14.8 cm body at 14.39 cm —
1.01 and 0.97 body diameters, log-log slope **0.948 [0.474, 1.897]**, excluding 0
and containing 1. *Grade: SUGGESTED. Two usable body sizes; the third does not
aggregate at this start radius and its unrestricted argmax is 2.02 diameters,
which drops the slope to 0.474; and three body-scaled lengths — the body as an
obstacle, the cluster link distance at 1.5 body diameters, and the occlusion
footprint — are not separated. Section: §18.*

**A8. Terrain-tuning starts to pay above a threshold amplitude, and where that
threshold sits depends on the correlation length.** At θ_m = 0.6 the paired
difference between the flat-trained and terrain-trained rows is **+0.0659
[+0.0296, +0.0918]** at λ = 0.05 m and **+0.0421 [+0.0107, +0.0659]** at 0.10 m —
both disjoint from zero, with the terrain-trained row ahead — and **−0.0160
[−0.0305, +0.0043]** at 0.20 m, where the crossing has not happened yet. The
pre-registered rule claims the crossing only if it is disjoint at more than one λ;
it is disjoint at two of three. The sign flip sits between θ_m = 0.2 and 0.45 at
λ = 0.05 m, between 0.2 and 0.6 at 0.10 m, and between 0.45 and 0.9 at 0.20 m.
*Grade: SUGGESTED. Three correlation lengths, all evaluated with rows trained at
one of them (†); the crossing's location is read off an eight-point θ_m grid, not
solved for; and **no mechanism is offered** — the obvious one, "shorter λ is a
rougher problem", is contradicted by the anchor's own tax being lower at
λ = 0.05 m (2.0719) than at 0.10 m (2.1492), because §15 puts the difficulty peak
at 7.46 cm between them. Sections: §24, §13 row 176.*

**A9. The terrain bit's standing against S = 2 improves monotonically as n
falls.** Hold ratios at λ = 0.10 m, θ_m = 0.9: **1.21 vs 1.10 at n = 20; 1.13 vs
1.04 at n = 50; 1.05 vs 1.14 at n = 10, overlapping.** Untested mechanism: fewer
neighbours to use as landmarks at small n. *Grade: OBSERVATION. Sections: §23.*

> This belongs with **P4 of the introduction** — the framework already says `c*`
> depends on `n`, and this is that dependence showing up in the one place the
> paper has a capability comparison to make it in. It is not a Limitations entry
> and must not be filed as one. It remains an observation: the n = 10 column is
> the *transferred* S = 4 row (see A1), the intervals overlap, and no mechanism
> was tested.

### B. Pursuer (active hostility)

**B1. Confusion acts through aggregation, and a dispersive control proves it.**
As κ goes 0 → 5, the two aggregating rows multiply mean survival by **×3.05** and
×2.23 (h = 0.39 s) and **×4.10** and ×1.91 (h = 1.93 s), while a row with
byte-identical pursuer sensing and no clustering gains **×1.20** and **×1.13**.
*Grade: SUPPORTED. Section: §8.*

**B2. Handling time is what makes dilution exist, and it sharpens the effect in
the predicted direction.** With capture free on contact a packed cluster is a
buffet. Raising handling from comparable to the pursuer's inter-neighbour travel
time (0.385 s) to 5× it grows the blind row's κ-response from ×3.05 to ×4.10 while
the dispersive row's shrinks. *Grade: SUPPORTED. Section: §8, correction #7.*

**B3. Beyond a pursuer range of about half the start radius, not aggregating wins,
and by a lot.** Survival pooled over κ at h = 1.93 s: at r_p = 0.35 m (0.47 R) the
blind row is at 0.00 [0.00, 0.23] and the dispersive row at 0.65 [0.60, 0.65]; at
0.60 m (0.81 R), 0.00 against 0.50; at 1.00 m (1.35 R, the perfect-perception
corner) 0.00 against 0.35. Confusion narrows the gap — mean survival at κ = 5 is
0.592, 0.628, 0.666 — but does not close it. *Grade: SUPPORTED for the ordering
over this grid; the rows compared are hand-designed ‡, so it is a claim about
spatial strategy, not about what S = 3 sensing can achieve. Section: §8.*

**B4. One sensor state — telling a pursuer from a robot — is worth more than
anything else on the capability axis in this family.** Median survival fraction
over the grid: B0 **0.350** [0.300, 0.375], B1 **0.650** [0.600, 0.700], B3
**0.700** [0.650, 0.750]. The blind row is wiped out at κ = 0 for every range
beyond 0.10 m while any row that can see the pursuer keeps 3–18 robots.
*Grade: SUGGESTED — B1 and B3 are hand-designed ‡, so this is a lower bound on
what S = 3 offers, not a measurement of it. Section: §5.*

> **Upgraded to SUPPORTED † by experiment 1 (§22), and split in two.** The
> capability claim — the one that goes in the abstract — is against **B0**, and is
> stated exactly as follows:
>
> > One additional sensor state buys survival at fixed task quality: the
> > best-of-three searched S = 3 row † beats the S = 2 Gauci row in 18 of 25
> > held-out cells at h = 1.93 s (0 worse; per seed 18 / 17 / 14), holding
> > dispersion among survivors at 1.41 vs 1.45.
>
> **The per-seed counts travel with the best-of-three number everywhere it
> appears** — register, abstract, figure captions, findings. They are the reader's
> window on the selection bias and there is no version of this sentence that drops
> them.
>
> The secondary claim, **G4′**, is against B1-ternary ‡ and is regime-specific:
> the searched row beats it in 13 of 25 cells, which is a thin pass honestly
> described rather than a moved threshold. Its job in the paper is the sentence
> *"the hand-designed rows are close to what a class search finds"*, which is
> itself useful. **B1's own 19/25 against B0 was strong evidence about a guess;
> the upgrade here is provenance, not margin.**
>
> Robustness (§25): the orderings against **B0 do not flip in any of the ten
> pseudo-reality models** at r_p = 0.1 and 0.35 m. Against **B1** at r_p = 1 m —
> the perfect-perception corner — the ordering flips in 5 of 10, all five of them
> models drawn at the finer control period. So the fragility lands on G4′ and not
> on G4, and it bounds G4′ rather than retracting it.

**B5. Survival alone is the wrong axis; on two axes there is a regime where
aggregation dominates outright.** The dispersive row's dispersion is **380–505**
against 1.43–1.63 for every aggregating row. At r_p = 0.35 m (0.47 R), κ = 3
every aggregating row beats it on **both** coordinates — survival 0.80–0.85
against 0.65 — so it is Pareto-dominated there. *Grade: SUPPORTED. Section: §12,
correction #12.*

**B6. r_p is only interpretable against the start radius.** At R = 0.74 m the
r_p = 1.0 m column is 1.35 R — the pursuer sees the whole starting swarm from
anywhere in it — so it is the degenerate corner, not the hard end of the axis.
*Grade: SUPPORTED (definitional, enforced in the plotting layer). Sections: §5,
§8, §12.*

**B7. A K = 1 (communication) row was never run.** Communication is not wired;
`rx` is held at 0, so such a row would silently behave as K = 0. *Grade: N/A —
recorded so the paper does not imply coverage it does not have.*

### C. Methodology

**C1. A controller searched at one operating point can be worse than the published
constants at another.** Two rows searched at n = 20, R = 0.74 m are worse than
Gauci's on flat ground at n = 50 at **every** start radius (paired ratios 0.973,
0.870, 0.775 and 0.944, 0.818, 0.777, all intervals below 1), and six times the
trial length does not close it (0.775 → 0.839 [0.795, 0.880] while Gauci's own
dispersion moves 1.204 → 1.209). At four times the training radius under terrain
and at τ = 3600 s, S2-rough forms a cluster in **34%** of runs against Gauci's
**100%**. *Grade: SUPPORTED. Section: §14.*

**C2. The trade is gathering rate against holding quality, and it is monotone in
R₀.** Median time to first cluster on flat ground at 3.0 m, n = 20, across five
rows: **140 s** (R₀ 14.45 cm), **245 s** (7.47), **280 s** (5.53), **330 s**
(4.74), **340 s** (4.47). The blind state *is* the search behaviour, so a smaller
turning circle holds a formed cluster better and covers ground more slowly.
*Grade: SUPPORTED as an association across five rows; the causal reading is
SUGGESTED, since R₀ was never swept as a dial in its own right. Sections: §14,
§19.*

**C3. Searching over the mission class rather than one arena produces a
controller that transfers.** S2-class-flat † matches or beats the published
constants on dispersion in **every** cell of the grid at matched trial length
(10 W, 2 tied, 0 L) and on reach in ten of twelve, losing reach only at the
largest start radius under terrain (0.86 against 1.00 at n = 20, 0.95 against 1.00
at n = 50). It is the only searched row that does not lose on flat ground at
n = 50: 1.026, 1.016, 0.999. *Grade: SUPPORTED for the cell-by-cell comparison;
the ingredients (scale-free aggregation over conditions, budget scaled to class
size) are SUGGESTED as necessary, since neither was ablated. Section: §19.*
**§21 qualifier.** The claim survives replication and is strengthened by it —
three independent searches, every one beating the enumerated reference in at
least 9 of 12 cells, all three fixing the n = 50 flat-ground failure — but the
*identity* of the transferring controller does not. R₀ spans 16.9% across the
three seeds and 4 of 12 held-out cells contain a disjoint pair, so the paper must
say "a class search reliably produces a transferring controller" and not "the
class search produces *this* controller". The baseline is best-of-three † per
cell.

**C4. A training objective must be re-scored at high replication before it is
quoted, and a searched row's standing must rest on held-out evaluation.** Two
independent demonstrations: the warm-started S = 4 search reported a training
objective of **1.2595** against 1.3012 and 1.3009 for its comparators and had no
advantage at all on held-out seeds; and the τ-corrected class search reported
**1.6009** where an honest 100-run re-score of the same constants gives
**2.6553**. *Grade: SUPPORTED. Sections: §10, §20.*

**C5. The noise-floor rule: check whether any one condition's per-evaluation
estimate is noisier than the differences the search must resolve.** At the worst
condition the 5th–95th percentile of the 2-run estimate the search actually saw
spans **2.79 log units** (6.98 → 114.07) against a **0.48 log unit** gap between
the row the search returned and a better one that already existed — noise **5.8×**
the signal. The remedy is runs per condition or a variance-stabilising statistic,
**not** a longer trial: raising τ turned uniform failure into outcomes spanning two
orders of magnitude, which is more gradient *and* far more variance.
*Grade: SUPPORTED for the measurement and for the failure it explains; SUGGESTED
that the remedy works, since it was not run. Section: §20.*

**C6. A control that isolates "searched" from "more capable" is necessary.**
Without S2-searched, §7's data reads as "the terrain bit cuts degradation from
2.21 to 1.22" — a large apparent win for extra sensing, and wrong. *Grade:
SUPPORTED (constructive demonstration). Section: §7.*

**C7. Reach and hold are different measurements and a threshold on the wrong one
sees nothing.** Reach is 1.00 in every terrain cell except one runaway corner, and
across a link distance from 2.2 to 6.0 body radii dispersion does not move at all
(**1.3875**) while the share of time reading as one cluster climbs **0.475 →
0.967** (F1-corrected; see §13 rows 13–14).
Reach is a proportion, so its median is 1 whenever the majority succeed — a median
panel draws a flat line at 1 while the probability falls, and the first version of
one figure did exactly that. *Grade: SUPPORTED. Sections: §2, §7, validation §3,
correction #6.*

---

## 7. Claims register

**Grades.**

* **SUPPORTED** — disjoint confidence intervals, or a replicated measurement, or
  a pre-registered decision rule that fired. Statable plainly.
* **SUGGESTED** — overlapping intervals, a single geometry, a post hoc window, a
  single optimiser seed, or an association without a controlled cause. Must be
  hedged in the wording given here.
* **NOT SUPPORTED** — a reading the data once seemed to support and no longer
  does. Listed so it cannot creep back into the paper.

Never upgrade a grade. Where a settled phrasing is given, use it verbatim.

**G4 in particular.** The pursuer sensor-state claim is SUGGESTED and stays
SUGGESTED. **No abstract, contribution list, discussion or conclusion may state
it without its hedge** — that every row above the blind one is hand-designed ‡,
so it is a lower bound on what S = 3 offers rather than a measurement of it. A
place where the sentence is too short for the hedge is a place where the claim
does not belong.

### SUPPORTED

| # | claim | sections |
|---|---|---|
| S1 | Along the terrain dial, over 0 ≤ θ_m ≤ 0.9 at λ/R₀(gauci) = 0.69, the capability minimum does not move: `c = (2,0,0,0)` suffices at every point, at start radius 0.74 m and at 1.5 m. | §9, §13, §14 |
| S2 | No S = 4 controller better than the searched S = 2 one was found at equal budget, including when warm-started at the S = 2 optimum. | §7, §10 **Split by swarm size after §23**: SUPPORTED † at n = 20; at n ∈ {10, 50} the n = 20-searched S = 4 rows are not disjointly better than the best S = 2 row, SUGGESTED † — candidates transferred, not searched at those n, margin 0.0069 at n = 10. Holds in 9 of 10 pseudo-reality models; model 09 reverses it (§25). |
| S3 | A hand-built S = 4 composite that switches between the two S = 2 rows is worse than either at every θ_m, and reproduces Gauci exactly on flat ground. | §9 |
| S4 | Terrain is a performance tax whose size depends mainly on how well matched the controller is: hold ratios **2.149 [1.853, 2.455]** (Gauci), **1.200 [1.124, 1.272]** (S2-flat), **1.099 [1.044, 1.145]** (S2-rough) at θ_m = 0.9, paired per run index. The matched-controller cost is therefore **10–20%**: 1.099 for the rough-trained row and 1.200 for the flat-trained one. | §13 |
| S5 | Of the Gauci → S2-rough gap at θ_m = 0.9, 96.9% is objective-tuning and 3.1% terrain-tuning at R = 0.74 m, against 99.7% / 0.3% at 1.5 m. The decomposition is a **level** statistic (medians of dispersion, which are additive) and is unaffected by the hold-ratio definition; the paired test on the terrain term is what carries its uncertainty, and **the term is not distinguishable from zero at either radius**: 0.0818 [−0.0008, 0.1331] at 0.74 m and −0.0124 [−0.1116, 0.0775] at 1.5 m. | §13, §14 |
| S6 | A scalar speed field produces no degradation at all (pooled 0.980 [0.976, 0.986], no peak, flat within [0.96, 1.01]) where the per-wheel field peaks at 2.21 [1.90, 2.41]. | §6 |
| S7 | The heading-rate residual is the first-order per-wheel traction effect: slope 0.9943, R² 0.9999 at ℓ/λ = 0.128. | §11, §16 |
| S8 | The quality of that linearisation collapses on ℓ/λ: max slope spread 0.0201 at matched ℓ/λ across a 4× range of λ, against a 0.86 range along the trend. | §16 |
| S9 | **Peak LOCATION does not scale with R₀.** Two controllers differing threefold in R₀ peak at the same λ in metres (7.46 cm), and inside one controller family a doubling of R₀ moves the peak by 1.39 [0.72, 1.93] — an interval excluding the ratio law's 2.00 and containing a fixed scale's 1.00. | §15, §17 |
| S9b | **Peak MAGNITUDE does scale with R₀, and not with the axle.** At θ_m = 1.0, varying the axle fourfold at fixed R₀ moves peak degradation by **44%** (2.21 / 2.74 / 3.18); varying R₀ fourfold at fixed axle moves it by **648%** (1.65 / 2.74 / 12.37). *(F2-corrected in freeze lift 1; the ordering and the claim are unchanged, and θ_m = 1.0 is outside the paper's stated range.)* **S9 and S9b are separate results about separate quantities and must never be run together into one sentence**: R₀ sets *how bad* the worst case is and does not set *where* it is. | §4 |
| S10 | Confusion acts through aggregation: κ 0 → 5 multiplies aggregating rows' survival ×3.05 and ×4.10 while a dispersive control with identical sensing gains ×1.20 and ×1.13. Under mean per-robot survival with Wilson intervals on 10 000 robots per cell the multipliers are unchanged and **every κ = 0 interval is disjoint from its κ = 5 interval** (B0 0.1796 → 0.5481 and 0.1444 → 0.5923; D 0.5300 → 0.6383 and 0.5912 → 0.6662). | §8 |
| G4 | **One additional sensor state buys survival at fixed task quality: the best-of-three searched S = 3 row † beats the S = 2 Gauci row in 18 of 25 held-out cells at h = 1.93 s (0 worse; per seed 18 / 17 / 14), holding dispersion among survivors at 1.41 vs 1.45.** The row is searched, so † : an upper bound on what S = 3 offers. The per-seed counts travel with the best-of-three number wherever it appears. | §22, §25 |
| S11 | With survival pooled over κ at h = 1.93 s and measured as mean per-robot survival with Wilson intervals, the matched pair crosses **between 0.27 R and 0.47 R**: the ternary row ‡ wins at 0.14 R (0.8788 [0.8723, 0.8851] against 0.8621 [0.8552, 0.8687], disjoint), the two overlap at 0.27 R (0.7369 [0.7282, 0.7454] against 0.7442 [0.7356, 0.7527]), and the dispersive row ‡ wins from 0.47 R outward (0.4875 [0.4777, 0.4973] against 0.6238 [0.6143, 0.6332], disjoint). Confusion narrows the gap but does not close it. The κ is part of the claim: at a fixed κ = 3 the ordering at 0.47 R reverses (S12). | §8 |
| S12 | At r_p = 0.47 R **and** κ = 3 the dispersive row ‡ is Pareto-dominated: every aggregating row beats it on both survival and the base task. Under mean per-robot survival with Wilson intervals all four aggregating rows are **disjointly above** it (0.7575, 0.7565, 0.7765, 0.7620 against 0.6510), so the claim strengthens rather than weakens. | §12 |
| S13 | Survival and base task differ by two orders of magnitude between strategies (380–505 against 1.43–1.63), so Idea B must be reported on two axes. | §12 |
| S14 | A controller searched at one operating point can be worse than the published constants at another, and a longer trial does not fix it. | §14 |
| S15 | Class-searched S2-class-flat † matches or beats the published constants on dispersion in every cell at matched trial length (10 W, 2 tied, 0 L) and loses reach only at the largest start radius under terrain. | §19 |
| S16 | A training objective is the minimum of a noisy sample: reported 1.2595 with no held-out advantage (§10), and reported 1.6009 against an honest re-score of 2.6553 (§20). | §10, §20 |
| S17 | At the worst training condition, the 2-run estimate the search saw spans 2.79 log units against a 0.48 log unit signal — noise 5.8× the signal. | §20 |
| S18 | Reach and hold are different measurements: reach is 1.00 in every terrain cell except one runaway corner, and dispersion is invariant to the link distance while cluster metrics are not. | §2, §7, validation |
| S19 | The published derived quantities reproduce: R₀ = 14.45 cm to 5e-5 m, ω₀ = −0.75 and ω₁ = −5.02 rad/s to 5e-3 rad/s. | validation |
| S20 | Correlated and i.i.d. dropout must be compared at matched **realised** rate: at a nominal 0.6 the realised rate is 0.89, and most of the apparent difference disappears when binned by realised rate. | §1 |
| S21 | H1 is null across three independent tests: actuation noise, the coarse terrain grid, and a dense 200-runs/cell neighbourhood of zero in which 0 of 23 cells has an interval disjoint from baseline. | §2, §3, ADR 0004 |
| S22 | A class search reliably produces a controller that beats the enumerated reference across the grid — three independent optimiser seeds score 9/2/1, 10/0/2 and 10/1/1 W/L/tied — but the returned controllers scatter: R₀ spans 16.9% and 4 of 12 held-out cells contain a disjoint pair, so no single row is *the* baseline. | §21 |

### SUGGESTED — with the wording to use

| # | claim | required hedge | sections |
|---|---|---|---|
| G1 | The worst correlation length **is** the body diameter. | "Peak λ tracks body diameter over a 2× range (1.01 and 0.97 diameters, log-log slope 0.948 [0.474, 1.897]), on the two body sizes that aggregate at this start radius. Three lengths scale with the body and are not separated here: the body as an obstacle, the cluster link distance at 1.5 body diameters, and the occlusion footprint. Including the smallest body — which reaches a cluster in at most 72% of runs — lowers the slope to 0.474. No mechanism is proposed." | §18 |
| G2 | The length scale is *fixed* rather than sub-proportional in R₀. | "Proportionality is rejected; a weak sub-proportional dependence is not excluded — the point estimate is 1.39 with an interval spanning 0.72 to 1.93, and peaks are located only to a log grid of ratio 1.39." | §17 |
| G3 | S2-class-flat is a better point on the rough class's objective than the rough-trained row. | "**S2-class-flat is a better point on the rough objective than the rough-trained row** — 1.6456 against 2.6553 at 100 runs per condition on the rough search's own training seeds — which shows the search did not find its own optimum. It does not locate that optimum, so 'the objective prefers a large R₀' is not established." | §20 |
| G11 | The headline orderings survive a neighbourhood of the model. | "Pseudo-realities in the sense of Ligot & Birattari (2020), ten models sampled from a pre-registered seed around the design point. **Comparisons 1 and 3 are robust** (10/10 same sign, 10/10 disjoint; and 10/10 sign for all three rows). **Comparisons 2 and 4 are not established either way** — signs hold, intervals do not separate in enough models — which is not evidence of robustness and must not be written as if it were. **Comparison 5 is fragile in one ordering of fourteen**: the searched S = 3 row against B1 ‡ at the perfect-perception corner, flipping in 5 of 10. The family perturbs actuation noise, sensor dropout, contact-solver effort and timestep — *how carefully the simulator is integrated and how noisy its sensors are*, **not whether the model is right**. It is not a reality-gap study: no hardware, no ARGoS, no second simulator (§12.3)." | §25 |
| G4′ | The hand-designed S = 3 rows are close to what a class search finds. | "Regime-specific and best-of-three: the searched S = 3 row † beats B1-ternary ‡ in **13 of 25** held-out cells at h = 1.93 s (1 worse, 11 overlapping), holding dispersion among survivors at 1.40 against B1's 1.52. A thin pass, described as one — the pre-registered threshold was 12 cells and was not moved after the fact. At r_p = 1 m this ordering flips in 5 of 10 pseudo-reality models (§25), so it is bounded to the design model there." | §22, §25 |
| G5 | Smaller R₀ causes slower gathering. | "Time to first cluster is monotone in R₀ across the five rows measured (140, 245, 280, 330, 340 s at 3.0 m on flat ground for R₀ = 14.45, 7.47, 5.53, 4.74, 4.47 cm); R₀ was never swept as a dial in its own right, so this is an association across five controllers rather than a controlled measurement." | §14, §19 |
| G6 | The class-search ingredients (geometric-mean objective, doubled budget) are what made it work. | "Neither was ablated; the row that transfers used both." | §19 |
| G7 | More runs per condition would fix the class search's noise floor. | "The remedy follows from the measurement but was not run." | §20 |
| G8 | A scalar speed field aggregates ~2% better than flat ground. | "Pooled 0.980 [0.976, 0.986], an interval excluding 1.0. Reported and not chased; it is not in H1's direction and 2% is at the edge of what the design resolves." | §6 |
| G9 | The n = 3 / n = 4 reach dip is Daymude-style deadlock. | "Recorded, not claimed. n = 3 and n = 4 reach a single cluster far less often than n = 2 or n = 5 and the dip does not close with time; the simpler explanation is combinatorial, and distinguishing the two needs the deadlock configurations checked directly." | validation §2 |
| G10 | The axle acts as a spatial gradient sensor, connecting to Berg & Purcell. | "The exact decomposition shows the residual is `v·∂m/∂n + ω·(m(centre) − 1)`, so the axle does read a spatial difference — but the mean-traction term is roughly ten times the gradient term at these constants, and no temporal-versus-spatial comparison was run. Use as an observation, not a result." | §11 |

### NOT SUPPORTED — readings that must not return

| # | the reading | why it is dead |
|---|---|---|
| N1 | "Small amounts of terrain or noise help aggregation" (H1). | Three independent nulls; 0 of 23 cells in a 200-runs/cell neighbourhood of zero has an interval disjoint from baseline. Daymude et al.'s mechanism is contact-deadlock breaking in a discrete model, and this continuous model shows no sign of such a deadlock at n = 20. (§2, §3, correction #5) |
| N2 | "The terrain bit cuts degradation from 2.21 to 1.22." | True only without the S2-searched control. With it, the searched S = 2 row reaches 1.10 [1.08, 1.15] and the S = 4 row is *worse* with disjoint intervals. (§7) |
| N3 | "More sensor states hurt" (from B2 at S = 5 scoring below B1 at S = 3). | B2's table is a hand-written guess ‡. It says no good five-state controller was found by hand. (§5) |
| N4 | "Re-tuning solves the terrain problem." | It recovers the loss, but 96.9% of the recovery is objective-tuning and 3.1% terrain-tuning at R = 0.74 m — 99.7% / 0.3% at 1.5 m — and the terrain share reverses sign on flat ground. (§13, §14, correction #11) |
| N5 | "The re-searched controller is the better controller." | It is better only near the initial condition it was searched in; at 4× the training start radius it fails outright, and at n = 50 it is worse than the published constants on flat ground at every radius. (§14) |
| N6 | "The terrain effect peaks at λ/R₀ ≈ 0.7 for any controller." | Two controllers differing threefold in R₀ peak at the same λ in metres, and inside one family doubling R₀ moves the peak by 1.39× [0.72, 1.93], excluding 2.00. §4's result stands as measured for Gauci's R₀ and loses its generalisation. (§15, §17, correction #13) |
| N7 | "There is a trade-off between flat-trained and rough-trained controllers that a terrain bit could arbitrate." | The crossing exists at the tuned start radius and is gone at twice it — branch (b), not (c). (§13, §14) |
| N8 | "The rough class row failed because its training objective was truncated." | Removing the truncation moved R₀ from 4.47 to 4.44 cm and made the row slightly worse. The cause is the noise floor. (§19's diagnosis, refuted in §20) |
| N9 | "Correlated dropout is much worse than i.i.d. dropout." | At matched *realised* rate most of the difference disappears; the apparent gap is the nominal rate not being the realised one (0.89 at a nominal 0.6). A genuine extra penalty appears only above a realised ~0.8. (§1) |
| N10 | "Two robots always aggregate" (Gauci et al. Theorem 3), and any check built on it. | The proof is unsound (Steinberg & Solovey 2024); the same controller fails on 4.24% of two-robot trials. This repository's small-n gate row failed for two weeks because of it. (validation, correction #1) |
| N11 | "The θ_m = 1.25–1.5 band shows terrain destroying aggregation." | That band is wheel **stall**, not terrain: the field reaches \|f\| = 1 so the multiplier can reach zero and the robot pivots. Removed from the swept range. (§4, §6, correction #10) |
| N12 | "A wider sensor cone fixes the small-n failure." | It is not what Gauci did, and under the corrected criterion widening the cone makes n = 2 worse (reach 0.90 → 0.17). (validation §2) |

---

## 8. Corrections to the build doc, #1–#15

Each entry: what was believed, what replaced it, what forced the change, and the
wording now in force. The four the repository leads with, because they change the
plan rather than a citation, are **#7** (handling time is required), **#9** (the
scalar-field mechanism claim is confirmed), **#2** (the impossibility result is
the framing anchor) and **#11** (`c*(θ)` must be reported against a re-searched
baseline, and it is flat along the terrain dial).

**#1 — The Gauci n = 2 proof has been disproven.**
*Believed:* "Exhaustive grid search at 4 constants; **proof for n = 2**; empirical
to 1000."
*Forced by:* Steinberg & Solovey (2024), arXiv:2501.00390, who identify an unsound
implicit assumption — that a distance condition `d ≤ 2(R+r)` guarantees subsequent
aggregation, when two robots can satisfy it while travelling the same circular
perimeter without ever seeing each other — and report the controller failing on
**4.24%** of two-robot trials. They give an alternative controller
`u* = (−a, a, b, b)` with `a, b ∈ (0,1]` and a correct proof.
*In force:* "Exhaustive grid search at 4 constants; empirical to 1000. The
published n = 2 proof is unsound (Steinberg & Solovey 2024), who give a corrected
controller and proof."

**#2 — There is an impossibility result for the whole capability class.**
*Believed:* not in the build doc at all.
*In force:* for **any** bimodal controller in this class — memoryless, binary
line-of-sight, no communication — there exists a swarm size `n` and an initial
state for which it does not aggregate (assumptions: plastic collisions, no noise,
no slippage). This belongs in the framing section, not the reading list. It
sharpens rather than undermines the upper-bound rule: for one whole capability row
the minimum does not exist uniformly in `n`, so `c*` is a function of swarm size
as well as environment, and part of the answer to "minimality is ill-defined" is
now a theorem.

**#3 — Daymude et al.'s deadlock threshold is n > 3, and the quote matters.**
*Believed:* "Deadlock exists for n > 3 … (verify exact n before quoting)."
*In force:* verified; the parenthetical can be dropped. The practical caveat should
be quoted exactly, because H1 leaned on it: the deadlocks "are not observed in
practice due to inherent noise in physical e-puck robots — collisions and slipping
perturb the precise balancing of forces to allow robots to push past one another."
That is about breaking a **force balance in contact**, not exploration.

**#4 — Simulation parameters to state in the methods section.**
*In force, all verified and pinned by a test:* Enki, e-puck as a disk of diameter
7.4 cm, mass 152 g, inter-wheel distance **5.1 cm**, wheel velocities in
±12.8 cm/s; control cycle **0.1 s**, physics **10× per cycle**; line-of-sight
sensor is a **ray** from the front returning the first body it intersects,
**infinite range** (the paper separately proves a sufficiently long range is
necessary); derived turn radius **14.45 cm**, ω₀ = **−0.75 rad/s**,
ω₁ = **−5.02 rad/s**.

**#5 — H1 should be withdrawn, or narrowed to a mechanism this model does not
have.**
*Believed:* "small α and θ_m help, as motion noise did in Daymude et al."
*Forced by:* three independent nulls — actuation noise (per-wheel Gaussian, 0–20%
of max wheel speed, 50 runs/cell: no benefit at any n, n = 20 mildly harmed); the
coarse terrain grid (monotone degradation on both dials); the fine H1 sweep (α ≤ 3°,
θ_m ≤ 0.1, **200 runs/cell**: 0 of 23 cells with an interval disjoint from
baseline, whole grid within 1.385–1.430).
*In force:* either withdraw it, noting that terrain degrades monotonically with
the interesting structure in *which* dial and *at what length scale*; or narrow it
to "if the continuous model exhibits Daymude-style contact deadlocks, small α and
θ_m should relieve them" — a testable prediction that first requires showing the
deadlocks exist here. Nothing in this repository suggests they do at n = 20.
**It should not survive into Paper 1 as written.**

**#6 — Idea A's threshold belongs on dispersion, not on a cluster count.**
*Forced by:* reach is 1.00 in every cell of the Idea A grid except the runaway
corner; and dispersion is invariant to the link distance (**1.3875** from 2.2 R to
6.0 R) while the cluster metrics move a lot (**0.475 → 0.967**). (F1-corrected;
the invariance the decision rests on is unchanged.)
*In force:* the build doc lists dispersion first among Idea A's metrics already —
this makes that binding rather than a preference.

**#7 — Handling time is required, not optional.**
*Believed:* not in the build doc; the v1 fix gave the pursuer perception limits but
capture remained free.
*Forced by:* with zero handling time a packed cluster is a buffet — one robot per
control step, twenty gone in two seconds — so aggregation is maximally bad under
any metric, the v1 failure mode one level down.
*In force:* add `h` as a fourth pursuer dial alongside ρ, r_p and κ, and set it
**relative to the pursuer's travel time between neighbouring robots in a formed
cluster** (7.4 cm at 19.2 cm/s = 0.385 s). Measured effect: aggregating rows
multiply survival ×3.05 at h ≈ that travel time and ×4.10 at 5× it, while a
dispersive control with identical sensing gains ×1.13.

**#8 — A dispersive control row belongs in Idea B's design.**
*Believed:* rows B0–B4 all aggregate when no pursuer is in view.
*Forced by:* none of them can distinguish "the swarm aggregated" from "the
pursuer's perception is poor", so the headline question is not answerable by that
grid.
*In force:* add one row with identical pursuer sensing and no clustering. The
answer it gives also belongs in the framing: confusion helps aggregating rows 2–4×
and a dispersive row 1.1×, so the dilution mechanism is real; but over the swept
grid the dispersive row still survives better on average. Aggregation stops being
catastrophic; it does not become the better bet.

**#9 — The corrected terrain model is necessary, and there is now a control.**
*Believed:* the argument that a scalar speed field cannot deform one robot's path
relative to another's — correct, but never tested, and "cannot deform a
trajectory" is not the same claim as "cannot break aggregation".
*Forced by:* the paired mechanism test — per-wheel **1.175 [1.154, 1.190]**,
scalar-centre **0.980 [0.976, 0.986]**, the scalar field producing no degradation
anywhere and no peak at all.
*In force:* keep the argument and add the measurement. It converts a
methodological aside into a result.

**#10 — Report θ_m only up to 1/max|f|.**
*In force:* the field reaches |f| = 1, so at θ_m = 1 the multiplier can reach zero,
a wheel stalls and the robot pivots. Any sweep above that measures stall, not
terrain. Sweeps are cut at **θ_m = 0.9** and figures at 1.0.

**#11 — Re-tuning does not solve terrain; it hides terrain behind a much larger
objective mismatch, in one initial condition.**
*Believed (from §9):* "a re-searched four-constant controller beats Gauci's at
every θ_m" read as re-tuning solving the terrain problem.
*Forced by:* two controls. (i) The 2 × 2 control (§13): S2-flat, searched with the
same optimiser, budget and training seeds but never having seen terrain, gives a
decomposition of **96.9% objective-tuning and 3.1% terrain-tuning** at θ_m = 0.9,
**99.7% / 0.3%** at 1.5 m, with the terrain term reversing sign on flat ground and
costing 4.1%. (ii) The regime control (§14): at 4× the training start radius with
τ extended sixfold, S2-rough forms a cluster in 34% of runs against Gauci's 100%,
and at n = 50 both searched rows are worse than Gauci **on flat ground** at every
radius.
*In force, four consequences:* capability and parameters are different axes, and a
result reading "hostility θ requires capability c" is not established until the
cheaper capability has been re-searched *at that θ*; **a re-searched baseline row
is necessary but not sufficient — it must also be shown to transfer**; a
degradation curve measured on published constants is a statement about those
constants (2.208× against 1.195×, so ~2.2× overstates by about six for a
well-matched controller); and a flat frontier is a result, not a null, to be
stated with the initial conditions it was measured in. Two caveats travel with it:
beating Gauci on flat ground is a statement about **this repository's objective**
and not a claim that Gauci's exhaustive grid search was wrong; and every searched
row is an upper bound (†) — §14 shows *these two* controllers fail to transfer,
not that a four-constant controller cannot.
*Also states:* the crossing that would justify a terrain-sensing bit is a property
of one initial condition, not of the controllers.

**#12 — Report Idea B on two axes, not one.**
*Forced by:* survival alone cannot see what surviving cost — a dispersive row
survives best in two of three cells while scoring 380–505 on the base task against
1.43–1.63 for every aggregating row.
*In force:* report a Pareto front, survival against base-task performance among
survivors, with the dispersive row marked as the **end of the front** rather than
as a competitor. Note the regime (r_p = 0.35 m = 0.47 R, κ = 3) where the front
collapses and the aggregating rows dominate on **both** axes — that, not the
trade-off cells, is where "aggregation protects the swarm" is true without
qualification.

**#13 — H2's worst correlation length is not a ratio law; state it as a length.**
*Believed:* terrain bites hardest at λ/R₀ ≈ 0.7, which for R₀ = 4.74 cm predicts a
worst λ near 3.3 cm.
*Forced by:* §15 — both controllers peak at the same λ in metres, **7.46 cm**
(λ/R₀ = 0.52 and 1.57), with the searched row's hold ratio at its predicted worst λ
in the bottom half of its range; and §17 — inside one controller family, doubling
R₀ moves the peak by **1.39× [0.72, 1.93]**, excluding 2.00 and containing 1.00.
*In force:* keep H2 as the question — *is there a worst length scale?* — and report
the answer as a length, "worst at λ ≈ 7.5 cm in this arena", with λ/R₀ a derived
number rather than the statement. Present the R₀-relative form as the hypothesis
the measurement rejected. **What sits at 7.5 cm is the body diameter** (§18): 1.01
and 0.97 body diameters for the two body sizes that aggregate at all, log-log slope
0.948 [0.474, 1.897]. Recorded with **no mechanism proposed**, because three
lengths scale with the body and this sweep separates none: the body as an obstacle,
the cluster link distance (1.5 body diameters, a parameter of the *metric*), and
the occlusion footprint. The smallest body does not aggregate at this start radius
and is excluded by a pre-registered validity window; including it lowers the slope
to 0.474, which still rejects "the body is irrelevant".

**Wording now in force (Phase A).** The magnitude result and the location
result are stated separately, as S9b and S9. "R₀ and not the axle sets the
peak" is not a sentence this paper may use, because it reads as a claim about
location while its evidence is about magnitude.

**#14 — The ℓ/λ statement can now be made without its single-λ caveat.**
*Believed:* §11's ℓ/λ trend, measured by varying the axle at one λ, where "a
function of ℓ/λ" and "a function of ℓ" are indistinguishable.
*Forced by:* §16 — three axles crossed with three λ so the same ℓ/λ is reached by
different (ℓ, λ) pairs; matched ℓ/λ agrees to **0.0201** in slope over a 4× range
of λ, and to 0.0001 at ℓ/λ = 0.255.
*In force:* state the ℓ/λ result with its established range — 4× in λ, 4× in axle,
one decade of ℓ/λ, at θ_m = 0.9 — and keep it separate from #13. They govern
different objects: ℓ/λ governs the linearisation of one robot's turn rate; it does
not govern where a swarm's aggregation degrades worst.

**#15 — Search the mission class, not one arena — and report the class.**
*Believed:* a searched row is fitted at one operating point and reported as a
capability result.
*Forced by:* §14's transfer failures, and §19's constructive fix — the same four
constants searched against a six-condition class produce a row that matches or
beats the published constants on dispersion in every cell at matched trial length
and on reach in ten of twelve.
*In force, two ingredients and three reporting requirements.* Ingredients: a
**scale-free aggregation over conditions** (median dispersion spans about 1.2 to
tens, so an arithmetic mean is the hardest condition wearing a disguise; averaging
logs weights a proportional improvement equally everywhere and reduces to the
single-condition objective when the class has one member), and a **budget scaled to
the class, and stated** (1200 × 12 against 600 × 12, or "no transferring controller
exists" is confounded with "not enough evaluations"). Report: (1) **the class it
was searched over**, as explicitly as the architecture; (2) **the budget and how it
scales with class size**; (3) **whether any one condition's per-evaluation estimate
is noisier than the differences the search must resolve** — at the worst condition
here the 5th–95th percentile of the 2-run estimate spans **2.79 log units** against
a **0.48 log unit** gap between the returned row and a better one that already
existed, so best-so-far selection returns whichever candidate drew a lucky pair,
and the search's reported best (1.6009) sits below an honest 100-run re-score of
the same constants (2.6553). The remedy is runs per condition or a
variance-stabilising statistic, **not** a longer trial: raising τ turned uniform
failure into outcomes spanning two orders of magnitude, more gradient *and* far
more variance. Corollary: **a training objective must be re-scored at high
replication before it is quoted**, and a searched row's standing must rest on
held-out evaluation. Caveat: the class-searched row is still † and the published
constants remain the only **enumerated** row and still own the hardest corner —
largest start radius under terrain, where they reach a cluster in every run and the
searched row in 86%.

---

## 9. Limitations register, deduplicated

Status is **open** (still true and unaddressed), **closed** (an experiment
answered it, named), or **accepted** (true, will not be addressed in Paper 1, and
must appear in the paper's limitations section).

| # | limitation | sections | status |
|---|---|---|---|
| L1 | **Simulation only.** Tier 1 is a purpose-built simulator; Tier 2 (ARGoS) was specified in the plan and **never run**, and no hardware experiment exists. Every number in this paper is Tier 1. | all | **accepted** |
| L2 | **The reality-gap position.** Contact is positional relaxation, not contact dynamics; converged to 0.01% residual overlap by 32 passes, which is adequate for Tier 1 and is why Tier 2 exists in the plan. The automatic-design literature (Birattari lab) treats the reality gap as a first-class design constraint, and this repository has taken none of those steps: no ARGoS replication, no simulation-only perturbation study, no hardware. The paper should claim simulation results and say plainly that transfer is untested. | all | **accepted** |
| L3 | **Absolute dispersion is provisional.** The normalisation constant has not been checked against Gauci's published figures; a packed cluster is designed to score ~1 and the clean baseline lands at 1.40. Comparisons *between* cells share the normalisation and are unaffected, and every claim in this paper is such a comparison. | all | **accepted** (flagged in code at `metrics::dispersion` and in validation) |
| L4 | **Almost everything is n = 20.** The exceptions are the clean-arena scaling curve (n = 2–100) and the class-search grid (n ∈ {20, 50}). | most | **accepted** |
| L5 | **One correlation length in the main terrain results.** λ = 0.10 m throughout §§7, 9, 10, 11, 13, 14. | §7, §9–§14 | **closed** for the location of the peak (§15: λ = 2–20 cm; §17: 2–38.6 cm) and for the ℓ/λ collapse (§16: λ ∈ {5, 10, 20} cm); **open** for everything else measured at λ = 0.10 m |
| L6 | **Equal search budget across unequal dimensions.** 600 evaluations over 8 constants is a thinner search per dimension than 600 over 4. | §7 | **partly closed** — §10's warm start removes the *direction* of the confound (the S = 4 search started holding the S = 2 optimum) but not its magnitude; a budget scaled with dimension was never run |
| L7 | **Every searched row is an upper bound (†) from a diagonal-covariance optimiser at a fixed budget.** sep-CMA-ES cannot exploit correlations between constants; a stronger searcher could find more. | §7, §9, §10, §13, §14, §19, §20, §21 | **accepted** — this is the framework's own rule, not a defect |
| L8 | **Most pursuer rows are hand-designed (‡).** B1, B2, B3 and D are guesses. They support claims about *spatial strategy* and about what one hand-designed arrangement achieves, never about what S = 3 or S = 5 sensing can do. | §5, §8, §12 | **accepted** — no pursuer row was ever searched |
| L9 | **B4 (K = 1) was never run.** Communication is not wired; `rx` is held at 0. The paper covers S and M, not K. | §5 | **accepted** |
| L10 | **Some geometry rows are not buildable robots.** `axle-x2-R0-same` puts the wheel contacts outside the 7.4 cm body; `body-half` puts them outside a 3.7 cm body; `body-x2` is a 14.8 cm robot with a 5.1 cm axle. They exist to break confounds numerically and are labelled ‡ wherever they appear. `axle-x2` carries the ℓ/λ ≈ 1 and 2.04 points, so the shape of that curve past ℓ/λ = 1 rests on it. | §4, §11, §16, §18 | **accepted** |
| L11 | **Peaks are located to a log grid of ratio 1.39**, which for §17 is also the size of the effect being measured. A finer grid around 4–12 cm would separate 1.39 from 1.00; this one cannot. | §15, §17, §18 | **open** |
| L12 | **The validity window (reach ≥ 0.8) was fixed after seeing the 1.5 m sweep.** Its use there is post hoc and labelled; it was fixed in advance for the 0.74 m companion and for §18. | §17, §18 | **accepted, labelled** |
| L13 | **§18 rests on two usable body sizes.** A two-point log-log slope has a wide interval, and the third row's unrestricted argmax (2.02 diameters) would drop the slope from 0.948 to 0.474. | §18 | **open** |
| L14 | **Three body-scaled lengths are not separated**: the body as an obstacle, the cluster link distance (1.5 body diameters — a parameter of the *metric*), and the occlusion footprint. Packing fraction also moves with the body at fixed start radius (0.0125 / 0.05 / 0.20). | §18 | **open** — the separating sweep is a follow-up item |
| L15 | **Density is confounded with start radius and n.** Sweeps that pin the start radius break the constant-density convention on purpose: n = 50 at 0.74 m is 2.5× the density of n = 20 there. | §14, §19, §20, §21 | **accepted, named** |
| L16 | **τ was extended only in the 3.0 m cells.** The 1.5 m cells are at 600 s and carry the same unresolved rate component, smaller. | §14, §19, §20 | **open** |
| L17 | **Dispersion is compared within a cell only**; every cross-cell claim is a paired ratio at fixed (radius, n, θ_m, τ). Absolute dispersion is not comparable across n or across body size. | §14, §18, §19 | **accepted, method** |
| L18 | **The class is six points on two axes.** λ, θ_m, τ and the arena are fixed inside it, so "transfers" means "transfers across start radius and swarm size". | §19, §20, §21 | **open** |
| L19 | **The class-search ingredients were not ablated.** The row that transfers used both a geometric-mean objective and a doubled budget; neither was tested alone. | §19 | **open** |
| L20 | **One optimiser seed per class row in §19 and §20.** | §19, §20 | **closed for the flat class** by §21, which ran seeds 2 and 3 and found the baseline scatters; **open** for the rough class, and open for a second *structurally different* optimiser, which `docs/statistics.md` asks for and which three seeds of sep-CMA-ES do not provide |
| L21 | **The pursuer sweeps use one ρ, one targeting rule, one search strategy, one pursuer, and τ = 120 s.** Two of three targeting rules and one of two search strategies are implemented but were never swept. | §5, §8, §12 | **accepted** |
| L22 | **Saturation in the pursuer results.** 8.8% of runs in §5 and 29% in §8 ended in a wipeout, concentrated exactly where the claims are strongest; `survival_fraction` is pinned at 0 there and `time_to_wipeout` is reported instead. At the perfect-perception cell the base-task axis is not estimable for three of four aggregating rows. | §5, §8, §12 | **accepted, stated** |
| L23 | **Occlusion was run once and never revisited.** No capability row was searched under it. | §1 | **accepted** |
| L24 | **The pre-registered Friedman-with-post-hoc comparison across capability rows was never run.** The wrapper exists and raises rather than silently substituting a weaker test; no comparison has used it. All row comparisons in this paper are pairwise with bootstrap or Wilson intervals, or paired by run index. | all | **open — and it is a protocol deviation the paper must disclose** |
| L25 | **`T` was never pre-registered as a single number.** `docs/statistics.md` requires one per paper; the figures report several contours (T = 0.7, 0.8, 0.9) and the text reads frontiers off intervals instead. The contours show how the answer depends on the bar; they are not a substitute for the bar. | all | **open — protocol deviation, must be disclosed** |
| L26 | **The anisotropy lemma was never attempted.** The build doc wants a theorem of the form "aggregation holds if the anisotropy ratio is below f(R₀, sensor range)"; §§4, 11 and 16 narrow the target to f(λ, ℓ) and f(body diameter), and no analysis was done. | §4, §11 | **open** |
| L27 | **The n = 3 / n = 4 reach dip is unexplained.** Recorded, not claimed. | validation | **open** |
| L28 | **The scalar field's ~2% improvement is unexplained.** Pooled 0.980 [0.976, 0.986], a real interval excluding 1.0. | §6 | **open** |
| L29 | **Three §13 rows cannot be regenerated.** Rows 56, 57 and 58 came from four single-condition searches whose **optimiser seed was never recorded** — not in the config, not in the output, not in the run log. The simulator, the search code, the configs and the CLI defaults are all ruled out, and all five class searches reproduce bit-for-bit, so the gap is the missing seed alone. The published constants stand and a re-run is a different, equally valid draw. Every search from freeze lift 1 onward records seed, training base, budget, git hash and config hash. | §13, `verification-report.md` |
| L30 | **`p_lock` was a function of the timestep, and is now a disclosure.** The pursuer's acquisition probability was rolled once per control step, so `P(acquire in 1 s) = 1 − (1 − p_lock)^(1/dt)` and its lethality depended on `sim.dt`. Found by experiment 4, fixed bit-neutrally at `dt = 0.1` (twelve pursuit files byte-identical over 105 800 records), so **no published number moves**. What changes is what may be said: the pursuit results are calibrated at `dt = 0.1`, and §2.2's timestep-independence is about exact-arc motion integration and does **not** cover the pursuit. A residual 2.5% handling-time quantisation at `h = 1.93 s` is disclosed and not corrected, because correcting it would not be bit-neutral. | §25, §2.2, §11 |
| L31 | **The aggregation dynamics are themselves timestep-sensitive, in the enumerated row.** Noise-free, at n = 20 under terrain, S2-gauci's reach at θ_m = 0.9 falls from 0.9050 [0.8723, 0.9300] at `dt = 0.1` to 0.6150 [0.5664, 0.6614] at 0.05, disjoint, and its hold ratio rises 2.0739 → 2.9747. The record's own `timestep_convergence` sweep showed the same thing at n = 5 and `validation.md` §H-E quotes only the n = 2 dispersion column. Every published number is at `dt = 0.1`; what is limited is the claim of timestep-independence, not the numbers. | §25, validation §H-E |
| L32 | **`sim.dt` was in the pseudo-reality family, and it is a perturbation of the robot rather than of the world.** Five of the ten sampled models carry a control period the design point does not, which is not what a Ligot-style family is for. It cannot be removed retroactively; the registered ten-model counts stand and the two sub-families are reported separately (D10). Every flip of the fragile ordering is in the control-period half. | §25 |
| L33 | **Model 09 reverses A1.** In one of ten pseudo-reality models the terrain-bit row is disjointly *better* than the searched S = 2 row, at −0.055 [−0.088, −0.018], with no single-parameter cause. An upper-bound claim survives one reversal as a disclosure; it is named here so it is not found later. | §25 |
| L34 | **The λ decomposition measures transfer, not a λ-matched decomposition.** Both tuned rows in experiment 3 were trained at λ = 0.10 m. A terrain term that grows at 0.05 and 0.20 m is consistent with "the term is real everywhere" and with "part of it is a mismatch penalty", and the design cannot separate them. | §24 |

---

## 10. Figure inventory

`results/` and `figures/` are generated and are **not committed** (README:
"Generated; not committed. Regenerate from configs."). Every figure below
regenerates from the named script or CLI invocation against the named config.
"Paper-ready" means the figure supports a claim at the grade the register gives
it and its caption is current.

| file | script / command | section | rows and cells shown | claim supported | status |
|---|---|---|---|---|---|
| `gauci_scaling.png` | `harness/figures_gauci_scaling.py` | validation §1 | Gauci's constants, n = 2…100, 100 runs/cell | S19, the reproduction | **paper-ready** (methods) |
| `occlusion_shakedown_curve.png` | `harness/figures_occlusion_shakedown.py` | §1 | M0 tight, M1 ‡, FN rate × correlation | S20 | paper-ready (a methods warning) |
| `occlusion_shakedown_surface.png` | `harness/figures_occlusion_shakedown.py` | §1 | as above | S20 | paper-ready |
| `terrain_idea_a_surface.png` | (see the script column note below) | §2 | Gauci, α × θ_m grid | A-flatness of reach; the two dials differ | paper-ready |
| `terrain_idea_a_curve.png` | (see the script column note below) | §2 | as above | as above | paper-ready |
| `terrain_h2_r0_scaling.png` | (see the script column note below) | §4 first pass | four R₀ rows | superseded by the powered sweep | **superseded** — the first pass could not separate λ/R₀ from λ/axle |
| `terrain_h2_powered.png` | `harness/figures_terrain_h2.py` | §4 | five rows breaking the R₀/axle confound, θ_m to 1.0 | R₀ not axle sets the peak | **paper-ready with a caveat**: the ratio-law reading it supports is superseded by §15/§17; use it for the R₀-versus-axle result only, and the caption must keep the widest-axle note |
| `terrain_mechanism.png` | `harness/figures_terrain_mechanism.py` | §6 | per-wheel vs scalar-centre, paired seeds | S6, A4 | **paper-ready** |
| `terrain_h3_capability.png` | `harness/figures_terrain_h3_capability.py` | §7 | S2-gauci, S2-searched †, S4-terrain † | S2, A1 | **paper-ready** |
| `terrain_retune_cost.png` | `harness/figures_terrain_retune_cost.py` | §9 | four rows incl. S4-composite ‡ | S1, S3 | **paper-ready** |
| `terrain_warm_s4.png` | `harness/figures_terrain_retune_cost.py` | §10 | S2-searched †, S4 cold †, S4-warm † | S2 | **paper-ready** |
| `terrain_mechanism_regression.png` | `harness/figures_mechanism_regression.py` | §11 | five rows, ℓ/λ from 0.25 to 1.02 | S7 | **paper-ready** (superseded in coverage by §16's figure, which extends the range) |
| `terrain_tuning_control.png` | `harness/figures_tuning_control.py` | §13 | S2-gauci, S2-flat †, S2-rough †, θ_m grid, plus the paired-difference panel | S4, S5 | **paper-ready** |
| `terrain_regime_robustness.png` | `harness/figures_regime_robustness.py` | §14 | three rows × radius × n × θ_m, reach / dispersion / gather time | S14, C1, C2 | **paper-ready** |
| `terrain_decision_rule_regimes.png` | `harness/figures_decision_rule_regimes.py` | §13 + §14 | the paired flat−rough difference at 0.74 m and 1.5 m | N7 | **paper-ready** |
| `terrain_lambda_sweep.png` | `harness/figures_lambda_sweep.py` | §15 | S2-gauci, S2-rough †, λ 2–20 cm, λ and λ/R₀ axes | S9 | **paper-ready** |
| `terrain_lambda_collapse.png` | `harness/figures_lambda_collapse.py` | §16 | 3 axles × 3 λ, slope and R² against ℓ/λ | S7, S8 | **paper-ready** |
| `terrain_lambda_r0_family.png` | `harness/figures_lambda_r0_family.py` | §17 | three R₀ rows × two start radii × λ 2–38.6 cm, with the validity window drawn | S9, G2 | **paper-ready** |
| `terrain_lambda_body.png` | `harness/figures_lambda_body.py` | §18 | three body diameters × λ, plus peak λ against diameter | G1 | **paper-ready, SUGGESTED grade** |
| `pursuer_idea_b_surface.png` | `harness/figures_idea_b.py first_pass` | §5 | B0–B3 on the r_p × κ grid, r_p ticked in metres and start radii | G4, B6 | **paper-ready** |
| `pursuer_dispersive_kappa.png` | `harness/figures_idea_b.py dispersive` | §8 | B0, B1 ‡, D ‡ against κ at two handling times | S10, B2 | **paper-ready** |
| `pursuer_dispersive_surface.png` | `harness/figures_idea_b.py dispersive` | §8 | the same rows on the r_p × κ grid | S11 | **paper-ready** |
| `pursuer_pareto.png` | `harness/figures_pareto.py` | §12 | five rows at three cells, survival against base task | S12, S13 | **paper-ready** |
| `terrain_class_search.png` | `harness/figures_class_search.py` | §19 | five rows × radius × n × θ_m: reach, dispersion, gather time | S15, C3 | **paper-ready** |
| `terrain_class_tau.png` | `harness/figures_class_tau.py` | §20 | the objective probe, reach against τ, and the noise histogram | S16, S17, G3, N8 | **paper-ready** |
| `phase0_seed_reproducibility.png` | `harness/figures_seed_reproducibility.py` | §21 | three optimiser seeds + the reference: constants, held-out dispersion at both n, and the winner's-curse gap per seed | S22, C4, the best-of-three baseline rule | **paper-ready** |

**Caption conventions in force**, to be reused verbatim: every figure whose rows
include a non-enumerated controller carries the stamp "† searched, not exhaustive
— an upper bound.  ‡ hand-designed, not searched — no evidence about the
capability itself."; every Idea B figure ticks `r_p` in metres **and** in start
radii and draws the perfect-perception boundary at R = 0.74 m; every terrain
figure states λ, θ_m, n, τ, start radius and runs/cell; the widest-axle and
body-size rows carry their "not a buildable robot" note in the caption as well as
in the text.

---

> **The eleven ex-CLI rows, and what "the script" means for them.** Eleven of the
> figures above were attributed to a `swarm-figure` invocation with only the
> subcommand recorded and none of its arguments, so they could not be regenerated
> at all (`verification-report.md` D9). Each now has a committed script and this
> column names it. **The scripts are not byte-for-byte ports and cannot be**: there
> is no committed original to compare against, and the one reconstruction attempted
> during the verification pass differed from the committed PNG in 44% of pixels.
> What each script reproduces is the figure §10 *describes*. Written 2026-09-10 in
> the freeze-lift-1 Phase 0 regeneration; a later diff against a lost image is not
> a regression.

## 11. Literature

Venues and years as recorded in the repository. Eight titles and three
bibliographic entries were **supplied externally in the Phase A revision and are
marked 'title supplied externally — verify before submission'**; the repository
never checked them against the source text.

Venues and years as recorded in the repository. **"Verified"** means the
repository checked the claim or the parameter against the source text; **"not
verified"** means it is carried from the build doc's reading list and was never
independently checked here.

| reference | venue / year | role | verified? |
|---|---|---|---|
| Gauci, Chen, Li, Dodd & Groß, *Self-organized aggregation without computation* | **IJRR**, 2014 | The anchor: one binary LOS sensor, no memory, no arithmetic, four wheel-speed constants found by exhaustive grid search; state-0 motion is a circle whose radius is the controller's only intrinsic length scale. Every parameter in §2 of this file comes from it. | **verified** — parameters, sensor model, control cycle and the three derived quantities all checked against the text and pinned by a test |
| Steinberg & Solovey, *Impossibility of Self-Organized Aggregation without Computation* | **arXiv:2501.00390, submitted 31 December 2024** — cite the preprint, which is the verified source; the IEEE 2025 venue is **unverified** | Two roles. (i) Disproves Gauci et al.'s n = 2 proof and reports 4.24% two-robot failure — this is what resolved the week-1 gate. (ii) Proves that for **any** bimodal controller in this class there exists an `n` and an initial state for which it does not aggregate: the framing anchor making `c*` a function of swarm size. | **verified** (the specific unsound assumption and the 4.24% figure are quoted) |
| Daymude, Harasha, Richa & Yiu, *Deadlock and noise in self-organized aggregation without computation* | **SSS**, 2021 | Deadlock exists for **n > 3** under uniform deterministic motion; noise "perturbs the precise balancing of forces to allow robots to push past one another". Source of H1, and of the reason H1 does not transfer. | **verified** — the exact `n` and the practical caveat were checked and quoted |
| Gauci et al., *Clustering objects with robots that do not compute* | **AAMAS**, 2014 | The **ternary** LOS sensor (nothing / robot / object) — precedent for Idea B's "distinguish robot from pursuer" rung, so S = 3 is not a new capability. | not verified here |
| Özdemir, Gauci & Groß, *Shepherding with robots that do not compute* | **ECAL**, 2017 | The only minimal result with a non-cooperating agent in the arena; sheep are passive, ours pursue. | not verified here |
| Özdemir, Gauci, Bonnet & Groß, *Finding consensus without computation* | **RA-L**, 2018 | The programme generalises beyond aggregation. | not verified here |
| Johnson & Brown, *Evolving and controlling perimeter, rendezvous, and foraging behaviors in a computation-free robot swarm* | **EAI BICT**, 2015 | Perimeter, rendezvous, foraging in a computation-free swarm: more behaviours, same budget. | not verified here — **title supplied externally in the Phase A revision; verify before submission** |
| Brown, Turgut & Goodrich, *Discovery and exploration of novel swarm behaviors given limited robot capabilities* | **DARS 2016** (Springer volume 2018) | Capability-vector framing precedent. | not verified here |
| Hamann, *Swarm Robotics: A Formal Approach* | 2018 | Mean-field models; **assume homogeneous space** — which is what this paper perturbs. | not verified here |
| Schmickl et al., *Get in touch: cooperative decision making based on robot-to-robot collisions* (**Auton. Agents Multi-Agent Syst.** 18(1), 2009); Kernbach et al., *Re-embodiment of honeybee aggregation behavior in an artificial micro-robotic system* (**Adaptive Behavior**, 2009) — **BEECLUST** | 2009 | Must be cited **and distinguished**: minimal robots aggregating in an explicitly non-uniform environment, but there the heterogeneity is the *target* the swarm is meant to find; here it is a *perturbation* the swarm is meant to survive. Same mechanism class, opposite role. | not verified here — **title supplied externally in the Phase A revision; verify before submission** |
| Chung, Hollinger & Isler, *Search and pursuit-evasion in mobile robotics: a survey* | **Autonomous Robots**, 2011 | Idea B sits at the minimal-sensing corner of this literature and should say so. | not verified here |
| Olson, Hintze, Dyer, Knoester & Adami, *Predator confusion is sufficient to evolve swarming behaviour* | **J. R. Soc. Interface** 10(85), 2013 | **The source of the confusion mechanism**: attack success falls with the number of prey in the predator's sensing field. `p_lock = 1/(1 + κ·n_local)` follows it. | not verified here (the functional form is the repository's own instantiation) — **title supplied externally in the Phase A revision; verify before submission** |
| Olson, Knoester & Adami | **Artificial Life**, 2016 | Predator confusion, follow-up. | not verified here |
| Wood & Ackland | **Proc. R. Soc. B**, 2007 | Selfish herd / confusion. | not verified here |
| Holling, *Some characteristics of simple types of predation and parasitism* | **Canadian Entomologist** 91, 1959 | Handling time and the disc equation: the quantity that makes dilution exist. Cited by concept in correction #7; **no bibliographic entry exists in the repository**. | resolved — Holling 1959. **Title supplied externally — verify before submission.** — **title supplied externally in the Phase A revision; verify before submission** |
| Berg & Purcell, *Physics of chemoreception* | **Biophys. J.**, 1977 | At small scales temporal comparison beats spatial comparison. Relevant here only through the observation that the axle reads a spatial difference (§11); claim G10 is graded SUGGESTED and no temporal-versus-spatial experiment was run. | not verified here |
| Hunt, *Phenotypic plasticity provides a bioinspiration framework for minimal field swarm robotics* | **Frontiers in Robotics and AI**, 2020 | Phenotypic-plasticity position paper for minimal field swarms; motivation citation, no experiments. | not verified here — **title supplied externally in the Phase A revision; verify before submission** |
| Francesca et al., *AutoMoDe: a novel approach to the automatic design of control software for robot swarms* (**Swarm Intelligence** 8(2), 2014); Birattari et al., *Automatic off-line design of robot swarms: a manifesto* (**Frontiers in Robotics and AI**, 2019); Ligot & Birattari, *On mimicking the effects of the reality gap with simulation-only experiments* (**ANTS**, 2018) | 2014–2019 | Automatic design and the reality gap: design bias by restricting control software to predefined modules; the ARGoS / ≥30 runs / Friedman + post-hoc / sim-vs-real protocol this repository's statistics plan adopts. | not verified here — **title supplied externally in the Phase A revision; verify before submission** |
| Jakobi, Husbands & Harvey, *Noise and the reality gap: the use of simulation in evolutionary robotics* | **ECAL**, 1995 | Reality gap / minimal simulations. | not verified here — **title supplied externally in the Phase A revision; verify before submission** |
| Ros & Hansen, *A simple modification in CMA-ES achieving linear time and space complexity* | 2008 | **sep-CMA-ES**, the optimiser used for every searched row. Named precisely because the separable variant is weaker than full CMA-ES and therefore only loosens an upper bound. | not verified here |
| Graham & Sloane, *Penny-packing and two-dimensional codes* | **Discrete & Computational Geometry** 5, 1990 | The normalised-second-moment convention the dispersion metric follows. **No bibliographic entry exists in the repository.** | resolved — Graham & Sloane 1990. **Title supplied externally — verify before submission.** — **title supplied externally in the Phase A revision; verify before submission** |
| Insider adversaries (Byzantine robots in collective decision-making; FL poisoning in ROS2 swarms) | 2026 | Cited **to distinguish**: a different problem — corrupting information rather than removing robots. | not verified here; **[CITATION NEEDED: specific insider-adversary references]** |

---

## 12. Discrepancies and open items

### 12.1 Where the documents and the results files disagree

**Resolved in the Phase A revision.** What follows records the state before it,
so a reader can trace any number that was quoted from an earlier draft.

**D0 — what Phase A changed, and what it did not.**

| what | before | after |
|---|---|---|
| hold ratio, §13 rows | 2.208 / 1.195 / 1.104 (ratio of medians) | **2.149 / 1.200 / 1.099** (paired) |
| hold ratio, §7 rows | 2.21 / 1.10 / 1.22 | **2.149 / 1.099 / 1.212** |
| §6 per-wheel peak | 2.21 [1.90, 2.41] | **2.149 [1.853, 2.455]** |
| survival, §5 grid rows | median run-level 0.350 / 0.650 / 0.450 / 0.700 | **mean per-robot 0.4324 / 0.5851 / 0.5188 / 0.6079**, Wilson on 50 000 robots |
| survival at 0.47 R, h = 1.93 | 0.00 / 0.55 / 0.65 (medians) | **0.3636 / 0.4875 / 0.6238**, Wilson on 10 000 robots |
| n = 2 reach | 93% | **0.88** (the canonical cell; 93% was a noise-sweep probe) |
| n = 2 hold | "~10% still touching at τ" | **0.15** still touching; 0.10 is the *share of time* |
| realised FN rate at nominal 0.6 | "the mean is 0.89" | **the median is 0.89**; the mean is 0.856 |
| §4 peak counts | "four of five rows" | **four of five at θ_m = 0.7**; two of five at θ_m = 1.0 |
| §20's 1.6009 / 2.6553 | "the returned row" | **S2-class-rough-tau**; the untau-corrected row is 1.9302 / 2.3456 |
| decomposition | 96.9 / 3.1 and 99.7 / 0.3 | **unchanged** (a level statistic), plus a paired test showing the terrain term includes zero at both radii |
| κ multipliers | ×3.05, ×4.10, ×2.23, ×1.91, ×1.20, ×1.13 | **unchanged**, and now every κ = 0 interval is disjoint from its κ = 5 interval |

**Grades that moved.** None down. **S10 and S12 strengthen** under the per-robot
Wilson statistic: S10's six κ-responses all have disjoint endpoint intervals, and
S12's four aggregating rows are all disjointly above the dispersive row rather
than merely above it. **S11 changes content, not grade**: the matched-pair
crossover moves from "beyond 0.47 R" to **between 0.27 R and 0.47 R**, because
the median run-level statistic overlapped at 0.47 R (0.55 [0.45, 0.65] against
0.65 [0.60, 0.65]) where the per-robot statistic is disjoint (0.4875 against
0.6238). **S9 splits into S9 and S9b**, location and magnitude, which were
previously stated as one result.

**Why the survival statistic changed.** A survival fraction is a proportion of
robots. The median of a per-run proportion at n = 20 can only land on a
twentieth, so its bootstrap interval reports the grid rather than the
uncertainty — which is how the blind row at 0.47 R came to be published as
"0.00 [0.00, 0.23]" when 36% of its robots survive. Pooling robots and taking a
Wilson interval is the statistic `docs/statistics.md` already prescribes for
proportions, and it is what §14–21 use for reach.

#### The original 12.1, as written


**D1 — Two different statistics are both called "hold ratio".** This is the only
substantive doc/results disagreement found, and it is a definitional one rather
than an error.

* §§7, 9 and 13 compute the hold ratio as a **ratio of medians**: the median
  dispersion at θ_m divided by the median at θ_m = 0.
* §§14–21 compute it as the **median of the paired per-run ratio**, run index by
  run index, which is also what their bootstrap intervals are taken on.

Recomputed from `results/terrain_tuning_control.jsonl` at θ_m = 0.9, 100
runs/cell:

| row | as published in §13 (ratio of medians) | recomputed, ratio of medians | recomputed, median of paired ratios |
|---|---|---|---|
| S2-gauci | 2.208 [1.904, 2.410] | **2.2075** | **2.149 [1.853, 2.455]** |
| S2-flat † | 1.195 [1.146, 1.265] | **1.1951** | **1.200 [1.124, 1.272]** |
| S2-rough † | 1.104 [1.078, 1.150] | **1.1040** | **1.099 [1.044, 1.145]** |

The same pattern at §7's λ = 0.10 m, θ_m = 0.9 cell: published 2.21 / 1.10 / 1.22
against paired 2.149 [1.853, 2.455] / 1.099 [1.044, 1.145] / 1.212 [1.158, 1.251].

**Both are correct as stated in their own sections**, the ratio-of-medians values
reproduce to four decimals, and the largest disagreement is 2.7% (2.208 against
2.149). **findings.md is authoritative for each section as written.** For the
paper, use **one** definition; the paired ratio is the better statistic because
the interval is computed on the same quantity as the point estimate, and it is
what §§14–21 already use. If the paper quotes §13's 2.208 / 1.195 / 1.104 it must
not also quote §14's 2.149 / 1.200 / 1.099 as if they were a different cell —
they are the same 100 runs.

**D2 — §7's S2-searched R₀ is quoted as "4.7 cm" and elsewhere as 4.74 cm.**
Rounding, not disagreement. 4.74 cm is exact for the recorded constants.

**D3 — §13's L2 distance S2-flat ↔ S2-gauci is given as 0.516; recomputed from
the stored constants it is 0.515.** Rounding at the last digit.

**Everything else checked reproduces exactly**, including: §9's absolute
dispersions (1.427 [1.399, 1.467], 1.253 [1.234, 1.283], 3.150 [2.716, 3.439],
1.383 [1.350, 1.441]); §13's decomposition inputs (3.150 / 1.438 / 1.383); §6's
pooled per-wheel and scalar values to within bootstrap noise (1.178 [1.158, 1.193]
and 0.979 [0.973, 0.986] against the published 1.175 [1.154, 1.190] and 0.980
[0.976, 0.986] — the same runs, a re-seeded bootstrap); and every §8 pursuer
survival multiplier (×3.05, ×2.23, ×1.20, ×4.10, ×1.91, ×1.13).

### 12.2 Protocol deviations the paper must disclose

* **The pre-registered Friedman-with-post-hoc comparison across capability rows
  was never run.** `docs/statistics.md` requires it and the wrapper exists and
  raises rather than substituting a weaker test; no comparison in this paper used
  it. All row comparisons are pairwise with bootstrap or Wilson intervals, or
  paired by run index.
* **`T` was never pre-registered as a single number.** The protocol requires one
  per paper. Figures report several contours (T = 0.7, 0.8, 0.9) and the text
  reads results off intervals instead. The contours show how the answer depends on
  the bar; they are not the bar.
* **Two independent optimisers were never run**; the agreement check that
  `docs/statistics.md` asks for was done with **independent seeds of the same
  optimiser** (§21) rather than with a second optimiser.
* **Tier 2 (ARGoS, ≥ 30 runs, sim-vs-real) was never run.**

### 12.3 Things that do not exist and must not be implied

* No hardware experiment, no ARGoS replication, no reality-gap study.
* No K ≥ 1 (communication) row — `rx` is held at 0.
* No searched pursuer row: every Idea B row above B0 is hand-designed.
* No anisotropy lemma or any analysis; the build doc's theorem target was narrowed
  by measurement and never attempted.
* No absolute-dispersion check against Gauci's published figures.
* No occlusion result beyond the single shakedown sweep.

### 12.4 Follow-up (not Paper 1), verbatim from the next list

Carried forward and updated. Items 1 and 2 are now answered (§§15, 16); what
remains, plus what §§14–16 surfaced:

1. ~~**Does S2-searched hold up at a λ matched to its own R₀?**~~ **Answered in
   §15.** It does: both rows share a worst λ of 7.46 cm, so the terrain effect
   does not follow the controller down and §13's λ was near-worst for both.
2. ~~**ℓ/λ across more than one λ.**~~ **Answered in §16.** It collapses: 0.0201
   max slope spread at matched ℓ/λ over a 4× range of λ.
3. **The scalar-field row's ~2% improvement** (§6), pooled 0.980 [0.976, 0.986].
   Still unexplained, still small, still a real interval.
4. **A searched dispersive row.** §12's front is between hand-designed spatial
   strategies. Searching both ends would say whether the front is a property of
   the strategies or of two guesses.
5. **Where the D-vs-aggregating crossover sits in r_p.** §12 brackets it between
   0.2 and 0.35 m (0.27 R and 0.47 R) at κ = 3; a denser r_p axis would locate
   it. Worth doing at two start radii, since r_p is only meaningful relative to
   R and the whole grid slides when R changes.
6. **Row B4** — the received alarm bit — still needs communication wired, and the
   delivery model (broadcast radius vs line-of-sight) is itself a capability
   claim to be counted in `K`.
7. **Budget scaled with dimension**, as opposed to a warm start. §10 removed the
   direction of the equal-budget confound; scaling the budget would remove it.
8. ~~**A search whose objective spans initial conditions.**~~ **Answered in
   §19**, and it changed the baseline. ~~The τ-in-the-training-loop follow-up~~
   **ran in §20**: it did not produce a transferring rough-trained row, and it
   showed §19's diagnosis was wrong. What replaces it: **a class search with more
   runs per condition** — §20 measures the per-evaluation noise at the worst
   condition as 2.79 log units against a 0.48 log unit signal, so 12 runs over
   six conditions cannot resolve what the search is being asked to resolve.
   Raising runs/evaluation to 60 (10 per condition) at the same 1200 evaluations
   is a 5× compute increase and the obvious next attempt; a variance-stabilising
   statistic in place of the per-condition median is the cheaper alternative and
   is untested.
12. ~~**Seed spread on a class search.**~~ **Answered in §21**, and the answer is
    that the baseline scatters: R₀ spans 16.9% across three seeds and 4 of 12
    held-out cells contain a disjoint pair, so the baseline is best-of-three †
    per cell. What remains open is a **second, structurally different optimiser**
    — `docs/statistics.md` asks for two, and three seeds of one shares
    sep-CMA-ES's diagonal covariance, so a bias common to that family would not
    show up.
9. **Which body-scaled length the worst λ actually is.** §18 shows the peak
   tracking body diameter at 1.01 and 0.97 diameters, but the cluster link
   distance (1.5 body diameters) and the occlusion footprint scale with the body
   too. `metrics.cluster_link_radii` is a metric parameter rather than a physical
   one, so varying it at a fixed body separates the metric's definition of
   "together" from the robot — one sweep, and the obvious next one.
10. **The gathering-rate / holding-quality trade-off as an axis in its own
    right.** §14 reads it off two searched controllers. Sweeping R₀ directly at
    fixed everything else — time to first cluster against held dispersion — would
    turn an explanation into a measurement, and it is one sweep.
11. **Whether the ℓ/λ collapse survives outside one decade.** §16 covers
    λ ∈ {5, 10, 20} cm. Nothing in it licenses λ = 1 cm or λ = 1 m.

### 12.5 Freeze

The experimental record for Paper 1 is frozen at commit **`ce427a8`** — the last
commit that produced experimental data, and the freeze hash. `2b736de` *declared*
the freeze in this document and produced no data; it is recorded so the
declaration can be found and is not the freeze hash.
§1–§21 of `docs/findings.md` are the evidence base. No simulation was run in this
branch for Paper 1 after that commit.

---

## 13. Numbers to quote

Every number likely to appear in the paper, flat. "CI" is 95%; bootstrap for
continuous quantities, Wilson for proportions. "Source" is the findings section;
"commit" is the commit that produced the number.

| # | quantity | value | CI | unit | source | commit |
|---|---|---|---|---|---|---|
| 1 | e-puck body diameter | 7.4 | — | cm | model | `47a5dd5` |
| 2 | inter-wheel distance (axle) | 5.1 | — | cm | model, **corrected from 5.3** | `47a5dd5` |
| 3 | wheel speed limit | ±12.8 | — | cm/s | model | `47a5dd5` |
| 4 | control cycle | 0.1 | — | s | model | `e175acb` |
| 5 | state-0 turn radius R₀ (Gauci) | 14.45 | reproduced to 5e-5 m | cm | validation | `47a5dd5` |
| 6 | ω₀ | −0.75 | to 5e-3 rad/s | rad/s | validation | `47a5dd5` |
| 7 | ω₁ | −5.02 | to 5e-3 rad/s | rad/s | validation | `47a5dd5` |
| 8 | Gauci two-robot failure rate (Steinberg & Solovey) | 4.24 | — | % | correction #1 | `82c8d06` |
| 9 | pairs reaching connectivity at n = 2 | **0.88** | Wilson [0.80, 0.93] | — | validation §1 (`gauci_scaling`, the canonical cell) | `2441bfc` |
| 10 | pairs still touching at τ here | ~10 | — | % | validation | `47a5dd5` |
| 11 | reach at n = 2 / 5 / 10+ | 0.88 / 0.98 / 1.00 | — | — | validation §1 | `2441bfc` |
| 12 | clean-arena dispersion at n = 20 | 1.43 | — | — | validation §1 | `2441bfc` |
| 13 | dispersion invariance to link distance (2.2 R → 6.0 R) | **1.3875 at every value, spread exactly 0** | — | — | validation §3 | `2441bfc`, **corrected freeze lift 1 (F1)** |
| 14 | single-cluster share over the same range | **0.475 → 0.967** | — | — | validation §3 | `2441bfc`, **corrected freeze lift 1 (F1)** |
| 15 | field median \|f\| | 0.3476 | max 0.9998, p99 0.9332 | — | model | `c137593` |
| 16 | θ_m ceiling | 0.9 (sweeps), 1.0 (figures) | — | — | correction #10 | `42a746a` |
| 17 | traction floor | 0.05 | never binds in range | — | model | `e83675e` |
| 18 | H1 fine sweep: cells with an interval disjoint from baseline | **0 of 23** | — | — | §3 | `c137593` |
| 19 | H1 fine sweep: whole-grid range | 1.385–1.430 | — | — | §3 | `c137593` |
| 20 | occlusion: realised FN rate at nominal 0.6 (correlated) | 0.89 | — | — | §1 | `24ca1ac` |
| 21 | occlusion: correlated vs i.i.d. at matched realised 0.85–0.95 | 4.68 vs 3.32 | — | — | §1 | `24ca1ac` |
| 22 | H2: peak λ/R₀, four of five rows, **at θ_m = 0.7** | 0.69 | at θ_m = 1.0 only two of five | — | §4 | `9b0b994` |
| 23 | H2: peak-degradation spread, axle 4× at fixed R₀, **at θ_m = 1.0** | **44** | **2.21 / 2.74 / 3.18** | % | §4 | `9b0b994`, **corrected freeze lift 1 (F2)** |
| 24 | H2: peak-degradation spread, R₀ 4× at fixed axle, **at θ_m = 1.0** | **648** | **1.65 / 2.74 / 12.37** | % | §4 | `9b0b994`, **corrected freeze lift 1 (F2)** |
| 25 | mechanism: per-wheel pooled degradation | 1.175 | [1.154, 1.190] | — | §6 | `e83675e` |
| 26 | mechanism: scalar-centre pooled | 0.980 | [0.976, 0.986] | — | §6 | `e83675e` |
| 27 | mechanism: per-wheel hold ratio at λ = 0.10 m, θ_m = 0.9 (paired) | **2.149** | [1.853, 2.455] | — | §6 | `e83675e` |
| 28 | H3: hold ratio at θ_m = 0.9, S2-gauci (paired) | **2.149** | [1.853, 2.455] | — | §7 | `9af4707` |
| 29 | H3: S2-searched † (paired) | **1.099** | [1.044, 1.145] | — | §7 | `9af4707` |
| 30 | H3: S4-terrain † (paired) | **1.212** | [1.158, 1.251] | — | §7 | `9af4707` |
| 31 | H3: reach at the worst cell, S2-gauci | 0.86 | **[0.78, 0.91]** | — | §7 | `9af4707`; **interval restated Wilson per §12.1 D0 in freeze lift 1** — it had been a normal approximation, [0.79, 0.93], on the same 100 runs and the same point estimate |
| 32 | search budget, single-condition rows | 600 × 12 = 7 200 | — | runs | §7 | `9af4707` |
| 33 | R₀ after searching at θ_m = 0.9 | 4.74 | — | cm | §7, §13 | `9af4707` |
| 34 | Idea B: mean per-robot survival over the grid, B0 | **0.4324** | Wilson [0.4281, 0.4367], 50 000 robots | — | §5 | `9b0b994` |
| 35 | …B1 ‡ | **0.5851** | [0.5807, 0.5894] | — | §5 | `9b0b994` |
| 36 | …B2 ‡ | **0.5188** | [0.5144, 0.5232] | — | §5 | `9b0b994` |
| 37 | …B3 ‡ | **0.6079** | [0.6036, 0.6122] | — | §5 | `9b0b994` |
| 38 | Idea B wipeout share (§5 / §8) | 8.8 / 29 | — | % | §5, §8 | `9b0b994`, `c5203f4` |
| 39 | start radius at n = 20 | 0.74 | — | m | model | `e175acb` |
| 40 | r_p / R at r_p = 1.0 m | 1.35 | — | — | §5 | `c65abe2` |
| 41 | pursuer inter-neighbour travel time | 0.385 | — | s | §8 | `c5203f4` |
| 42 | κ-response, B0 at h = 0.39 s | ×3.05 | 0.180 → 0.548 | — | §8 | `c5203f4` |
| 43 | κ-response, B0 at h = 1.93 s | ×4.10 | 0.144 → 0.592 | — | §8 | `c5203f4` |
| 44 | κ-response, B1 ‡ | ×2.23 / ×1.91 | 0.258 → 0.575 / 0.328 → 0.628 | — | §8 | `c5203f4` |
| 45 | κ-response, D ‡ | ×1.20 / ×1.13 | 0.530 → 0.638 / 0.591 → 0.666 | — | §8 | `c5203f4` |
| 46 | mean per-robot survival at r_p = 0.35 m (0.47 R), h = 1.93, B0 / B1 ‡ / D ‡ | **0.3636 / 0.4875 / 0.6238** | [0.3542,0.3731] / [0.4777,0.4973] / [0.6143,0.6332], 10 000 robots each | — | §8 | `c5203f4` |
| 47 | D's state-0 arc | 99.45 (≈99) | — | cm | §8 | `c5203f4` |
| 48 | time to wipeout at r_p = 0.35 m, κ = 0, B0 | 46.6 | n = 94 | s | §8 | `c5203f4` |
| 49 | §9: dispersion at θ_m = 0, S2-gauci | 1.427 | [1.399, 1.467] | — | §9 | `f7376de` |
| 50 | §9: …S2-searched † | 1.253 | [1.234, 1.283] | — | §9 | `f7376de` |
| 51 | §9: dispersion at θ_m = 0.9, S2-gauci | 3.150 | [2.716, 3.439] | — | §9 | `f7376de` |
| 52 | §9: …S2-searched † | 1.383 | [1.350, 1.441] | — | §9 | `f7376de` |
| 53 | §9: …S4-composite ‡ | 1.999 | [1.861, 2.143] | — | §9 | `f7376de` |
| 54 | §9: S2-searched improvement on flat ground | 12.2 | — | % | §9 | `f7376de` |
| 55 | §10: S4-warm at the peak | 1.412 | [1.349, 1.503] | — | §10 | `6989a91` |
| 56 | §10: warm-start training objective | 1.2595 | — | — | §10 | `6989a91` |
| 57 | §10: cold S4 / S2 training objectives | 1.3012 / 1.3009 | — | — | §10 | `6989a91` |
| 58 | §10: warm-start L2 from its start | 0.464 | halves diverged ≤ 0.254 | — | §10 | `6989a91` |

> **Provenance note on rows 56, 57 and 58 — searched, optimiser seed not
> recorded, non-regenerable.** These three came from four single-condition
> searches whose optimiser seed is recorded nowhere: not in the config, not in
> the output JSON, not in the run log. Freeze lift 1 ruled out the simulator (the
> binary built at `9af4707` returns byte-identical constants to HEAD over the
> full budget), the search code, the configs and the CLI defaults, and confirmed
> that **all five class searches reproduce bit-for-bit** — so the gap is the
> missing seed and nothing else. A sanity check found the published rows to be
> ordinary draws: paired ratios against re-runs of 0.9832 [0.9380, 1.0139] and
> 1.0019 [0.9910, 1.0091], both including 1.
>
> **The published constants are the rows of record and are not replaced.** This
> is a disclosure, not a defect to hide: the numbers are right, and they cannot
> be regenerated from what was written down. Every search run from freeze lift 1
> onward records its optimiser seed, training seed base, budget, git hash and
> config hash in its output JSON (`swarm-cli/src/search.rs`), so no later row can
> arrive in this state. See `verification-report.md` for the four re-run
> controllers and the elimination, and §9 for the Limitations entry.
| 59 | §11: full-expansion slope at ℓ/λ = 0.25 | 0.976 | R² 0.9983 | — | §11 | `f73cc8a` |
| 60 | §11: at ℓ/λ = 0.51 (three rows, R₀ 4× apart) | 0.900 / 0.894 / 0.901 | agree to 0.007 | — | §11 | `f73cc8a` |
| 61 | §11: at ℓ/λ = 1.02 | 0.623 | R² 0.7373 | — | §11 | `f73cc8a` |
| 62 | §11: gradient-only slopes / R² | 0.52–0.81 / 0.02–0.28 | — | — | §11 | `f73cc8a` |
| 63 | §11: mean-traction term relative to gradient term | ~10× | — | — | §11 | `f73cc8a` |
| 64 | §11/§16: robot-timesteps pooled per point | 12 000 000 | — | — | §11, §16 | `f73cc8a` |
| 65 | §12: D's dispersion across cells | 379.9 / 386.3 / 504.8 | [344.3, 399.9] / [357.9, 431.3] / [432.9, 613.9] | — | §12 | `91b8d57` |
| 66 | §12: aggregating rows' dispersion | 1.43–1.63 | — | — | §12 | `91b8d57` |
| 67 | §12: mean per-robot survival at r_p = 0.47 R, κ = 3, four aggregating rows vs D ‡ | **0.7565–0.7765 vs 0.6510** | all four disjointly above D | — | §12 | `91b8d57` |
| 68 | §13: decomposition, objective-tuning share | **96.9** (99.7 at 1.5 m) | — | % | §13, §14 | `9fa30a5`, `d0d95c3` |
| 69 | §13: decomposition, terrain-tuning share | **3.1** (0.3 at 1.5 m) | — | % | §13, §14 | `9fa30a5`, `d0d95c3` |
| 70 | §13: terrain-tuning cost on flat ground | 4.1 | — | % | §13 | `9fa30a5` |
| 71 | §13: hold ratio at θ_m = 0.9, **paired** (the paper's single definition) | **2.149 / 1.200 / 1.099** | [1.853, 2.455] / [1.124, 1.272] / [1.044, 1.145] | — | §13 | `9fa30a5` |
| 72 | §13: the retired ratio-of-medians form, kept for traceability only | 2.208 / 1.195 / 1.104 | [1.904, 2.410] / [1.146, 1.265] / [1.078, 1.150] | — | §12.1 | `9fa30a5` |
| 73 | §13: crossing, S2-rough better at θ_m = 0.6 | +0.0421 | [+0.0107, +0.0659] | dispersion | §13 | `9fa30a5` |
| 74 | §14: same cell re-run at 1.5 m | −0.0008 | [−0.0134, +0.0433] | dispersion | §14 | `d0d95c3` |
| 75 | §14: paired ratio vs Gauci, θ_m = 0.9, n = 20, R = 0.74 m | 1.942 / 2.129 | [1.645, 2.267] / [1.807, 2.446] | — | §14 | `d0d95c3` |
| 76 | §14: …at 3.0 m, τ = 600 s | 0.296 / 0.137 | [0.170, 0.638] / [0.098, 0.210] | — | §14 | `d0d95c3` |
| 77 | §14: reach at 3.0 m, θ_m = 0.9, τ = 600 s | 0.46 / 0.23 / 0.11 | [0.37, 0.56] / [0.16, 0.32] / [0.06, 0.19] | — | §14 | `d0d95c3` |
| 78 | §14: the same at τ = 3600 s | 1.00 / 0.60 / 0.34 | [0.96, 1.00] / [0.50, 0.69] / [0.25, 0.44] | — | §14 | `d0d95c3` |
| 79 | §14: S2-rough paired ratio at τ = 600/1800/3600 s | 0.137 / 0.141 / 0.148 | — | — | §14 | `d0d95c3` |
| 80 | §14: n = 50 flat-ground paired ratios (0.74 / 1.5 / 3.0 m), S2-flat | 0.973 / 0.870 / 0.775 | [0.956, 0.979] / [0.834, 0.883] / [0.738, 0.834] | — | §14 | `d0d95c3` |
| 81 | §14: the same after τ = 3600 s | 0.839 | [0.795, 0.880] | — | §14 | `d0d95c3` |
| 82 | §14: gather time on flat ground at 3.0 m, n = 20 | 140 / 280 / 330 | [130,150] / [260,295] / [310,345] | s | §14 | `d0d95c3` |
| 83 | §15: shared peak λ | **7.46** | — | cm | §15 | `628570b` |
| 84 | §15: that peak as λ/R₀ | 0.52 (Gauci) / 1.57 (S2-rough †) | — | — | §15 | `628570b` |
| 85 | §15: hold ratio at the peak (paired) | 2.505 / 1.121 | [2.263, 2.822] / [1.090, 1.222] | — | §15 | `628570b` |
| 86 | §15: flat-ground invariance across eight λ | 1.4267 / 1.2530, spread 0 | — | — | §15 | `628570b` |
| 87 | §16: slope at ℓ/λ = 0.128 | 0.9943 | R² 0.9999 | — | §16 | `20d79b4` |
| 88 | §16: slope at ℓ/λ = 2.04 | 0.1351 | R² 0.0870 | — | §16 | `20d79b4` |
| 89 | §16: max slope spread at matched ℓ/λ | **0.0201** | 0.0001 at ℓ/λ = 0.255 | — | §16 | `20d79b4` |
| 90 | §16: that spread as a share of the trend's range | 2.3 | — | % | §16 | `20d79b4` |
| 91 | §17: peak ratio for a doubling of R₀ | **1.39** | [0.72, 1.93] | — | §17 | `9335c56` |
| 92 | §17: peaks, R₀ 7.23 / 14.45 cm | 5.37 / 7.46 | [3.86, 10.36] / [5.37, 7.46] | cm | §17 | `9335c56` |
| 93 | §17: R₀-x2 row's reach ceiling, and its flat-ground dispersion | 0.73; 2.902 | — | — | §17 | `9335c56` |
| 94 | §17: validity window | reach ≥ 0.8 at θ_m = 0.9 | — | — | §17 | `9335c56` |
| 95 | §18: peak λ / body diameter, 7.4 and 14.8 cm bodies | **1.01 / 0.97** | peaks 7.46 [5.37, 7.46] and 14.39 [10.36, 20.00] cm | — | §18 | `5b72abc` |
| 96 | §18: log-log slope of peak λ on body diameter | **0.948** | [0.474, 1.897] | — | §18 | `5b72abc` |
| 97 | §18: the same including the non-aggregating body | 0.474 | — | — | §18 | `5b72abc` |
| 98 | §18: smallest body's reach ceiling; flat-ground dispersion | 0.72; 3.057 | against 1.427 for the base body | — | §18 | `5b72abc` |
| 99 | §18: packing fraction across the three bodies | 0.0125 / 0.05 / 0.20 | — | — | §18 | `5b72abc` |
| 100 | §19: class budget | 1200 × 12 = 14 400 | double §9's | runs | §19 | `e6c4145` |
| 101 | §19: S2-class-flat R₀ | **7.47** | from S2-flat's 5.53 | cm | §19 | `e6c4145` |
| 102 | §19: S2-class-rough R₀ | 4.47 | from S2-rough's 4.74 | cm | §19 | `e6c4145` |
| 103 | §19: cell counts at τ = 600 s (W / L / tied) | 9 / 2 / 1 | S2-flat 7/4/1, S2-rough 7/5/0, S2-class-rough 7/5/0 | of 12 | §19 | `e6c4145` |
| 104 | §19: n = 50 flat-ground ratios, S2-class-flat | 1.026 / 1.016 / 0.999 | [1.020, 1.033] / [1.009, 1.023] / [0.991, 1.008] | — | §19 | `e6c4145` |
| 105 | §19: 3.0 m, n = 20, τ = 3600 s, S2-class-flat ratio | **1.436** | [1.249, 1.673] | — | §19 | `e6c4145` |
| 106 | §19: the same at n = 50 | 1.063 | [0.934, 1.172] | — | §19 | `e6c4145` |
| 107 | §19: reach there, Gauci vs S2-class-flat | 1.00 vs 0.86; 1.00 vs 0.95 | [0.96,1.00] vs [0.78,0.91]; [0.96,1.00] vs [0.89,0.98] | — | §19 | `e6c4145` |
| 108 | §19: gather time vs R₀, five rows | 140 / 245 / 280 / 330 / 340 | R₀ 14.45 / 7.47 / 5.53 / 4.74 / 4.47 cm | s | §19 | `e6c4145` |
| 109 | §20: R₀ before and after removing the truncation | 4.47 → **4.44** | — | cm | §20 | `3229c59` |
| 110 | §20: cell counts | 6 / 5 / 1 | against 7 / 5 / 0 | of 12 | §20 | `3229c59` |
| 111 | §20: reach at the targeted cell, τ = 3600 s | **0.26** | [0.18, 0.35] | — | §20 | `3229c59` |
| 112 | §20: objective re-score, S2-class-flat vs the returned row | **1.6456 vs 2.6553** | 100 runs/condition | — | §20 | `3229c59` |
| 113 | §20: the returned row's reported training objective | **1.6009** | against 2.6553 honest | — | §20 | `3229c59` |
| 114 | §20: 2-run estimate spread at the worst condition | **2.79** | 6.98 → 114.07 | log units | §20 | `3229c59` |
| 115 | §20: the signal it had to resolve | **0.48** | — | log units | §20 | `3229c59` |
| 116 | §20: noise-to-signal ratio | **5.8×** | — | — | §20 | `3229c59` |
| 117 | §20: dispersion range at that condition, 100 runs | 1.14 – 242.50 | quartiles 13.69 / 73.59 | — | §20 | `3229c59` |
| 118 | §21: R₀ returned by seeds 1 / 2 / 3 | **7.47 / 8.88 / 8.64** | spread 1.41 cm = **16.9%** of the mean | cm | §21 | `ce427a8` |
| 119 | §21: pre-registered agreement rule on R₀ | 10 | — | % | §21 | `ce427a8` |
| 120 | §21: held-out cells containing a disjoint pair of seeds | **4 of 12** | — | — | §21 | `ce427a8` |
| 121 | §21: cell counts against the reference, seeds 1 / 2 / 3 (W/L/tied) | 9/2/1, **10/0/2**, 10/1/1 | of 12, τ = 600 s | — | §21 | `ce427a8` |
| 122 | §21: L2 between seeds | 0.226 / 0.315 / 0.397 | s1↔s2, s1↔s3, s2↔s3 | — | §21 | `ce427a8` |
| 123 | §21: L2 seed 2 ↔ the reference | 0.252 | smaller than s2↔s3 | — | §21 | `ce427a8` |
| 124 | §21: reported training objectives, seeds 1 / 2 / 3 | 1.2143 / **1.1927** / 1.2120 | — | — | §21 | `ce427a8` |
| 125 | §21: honest re-scores of the same constants | 1.2338 / **1.2246** / 1.2301 | 100 runs/condition | — | §21 | `ce427a8` |
| 126 | §21: winner's-curse gaps | **+0.019 / +0.032 / +0.018** | against §20's +1.05 | — | §21 | `ce427a8` |
| 127 | §21: dispersion at 3.0 m, θ_m = 0.9, n = 20, τ = 600 s | 12.517 / **3.701** / 13.701 | reach 0.17 / 0.45 / 0.28 | — | §21 | `ce427a8` |
| 128 | §21: the same cell's paired ratio at τ = 3600 s | **1.436 / 1.430 / 1.441** | [1.249,1.673] / [1.311,1.746] / [1.224,1.753] | — | §21 | `ce427a8` |
| 129 | §21: reach there at τ = 3600 s, reference vs seeds | 1.00 vs 0.86 / 0.93 / 0.88 | — | — | §21 | `ce427a8` |
| 130 | §21: n = 50 flat-ground dispersion, three seeds at 3.0 m | 1.200 / 1.166 / 1.191 | disjoint pair present | — | §21 | `ce427a8` |
| 131 | §13: terrain-tuning term, paired per run at 0.74 m | **+0.0818** | [−0.0008, +0.1331] — **includes zero** | dispersion | §13 | `9fa30a5` |
| 132 | §13/§14: the same at 1.5 m | **−0.0124** | [−0.1116, +0.0775] — **includes zero** | dispersion | §14 | `d0d95c3` |
| 133 | §13: how much the anchor's hold ratio overstates the matched controller's | **1.96×** | 2.149 / 1.099, paired | — | §13 | `9fa30a5` |
| 134 | §13: dispersion recovered by matching the objective, as a share of the anchor's | **119%** | (3.1495 − 1.4379) / 1.4379 | % | §13 | `9fa30a5` |
| 135 | §8: mean per-robot survival, matched pair (B1 ‡ / D ‡) at 0.14 R, h = 1.93 | **0.8788 / 0.8621** | [0.8723,0.8851] / [0.8552,0.8687] — disjoint, aggregating ahead | — | §8 | `c5203f4` |
| 136 | §8: the same at 0.27 R | **0.7369 / 0.7442** | [0.7282,0.7454] / [0.7356,0.7527] — overlapping | — | §8 | `c5203f4` |
| 137 | §8: the same at 0.81 R and 1.35 R | **0.1295 / 0.5084** and **0.0655 / 0.3816** | all four intervals width < 0.02 | — | §8 | `c5203f4` |
| 138 | §8: mean per-robot survival, B0-blind at 0.81 R and 1.35 R, h = 1.93 | **0.0199** | [0.0173, 0.0228] at both | — | §8 | `c5203f4` |
| 139 | model: the incorrect axle length the build doc carried | 5.3 | corrected to 5.1 | cm | correction #4 | `47a5dd5` |
| 140 | literature: reach reported for this controller at n = 2 | ~95.8 | Gauci et al. 2014 | % | validation §1 | `2441bfc` |
| 141 | pursuer speed ρ·v_max | 19.2 | = 0.385 s between touching neighbours | cm/s | §8 | `c5203f4` |
| 142 | §3: H1 fine sweep, zero-slope row | 1.406 / 1.388 / 1.385 / 1.414 | [1.389,1.429] / [1.360,1.406] / [1.371,1.414] / [1.399,1.436] | — | §3 | `c137593` |
| 143 | §16: full-expansion slope at ℓ/λ = 0.255 | 0.9762 | R² 0.9983 | — | §16 | `f73cc8a` |
| 144 | §14: S2-flat at 3.0 m, θ_m = 0.9, τ = 3600 s, paired vs Gauci | 1.297 | [0.960, 1.495] | — | §14 | `d0d95c3` |
| 145 | §14: n = 50 flat-ground paired ratios (0.74 / 1.5 / 3.0 m), S2-rough † | 0.944 / 0.818 / 0.777 | every interval below 1 | — | §14 | `d0d95c3` |
| 146 | §21: honest re-score of the anchor on the flat class objective | 1.2905 | 6 conditions, 100 runs each | — | §21 | `ce427a8` |
| 147 | §21: winner's-curse gaps at full precision | +0.0194 / +0.0318 / +0.0181 | seeds 1 / 2 / 3 | — | §21 | `ce427a8` |
| 148 | §18: body-half packing fraction as a percentage of the base body's | 20.6 | 3.7 cm body | % | §18 | `9335c56` |
| 149 | §4: grid resolution of the powered sweep, λ from 1.25 to 40 cm | 2.6 | ratio between adjacent λ | × | §4 | `9b0b994` |
| 150 | constants, S2-gauci (state 0 \| state 1) | −0.7000, −1.0000 \| +1.0000, −1.0000 | enumerated | — | §4.1 | `47a5dd5` |
| 151 | constants, S2-flat † | −0.3289, −0.8923 \| +0.9983, −0.6589 | R₀ 5.53 cm | — | §4.1 | `9fa30a5` |
| 152 | constants, S2-rough † | −0.2852, −0.9495 \| +0.9354, −0.2262 | R₀ 4.74 cm | — | §4.1 | `9af4707` |
| 153 | constants, S2-class-flat † (seed 1) | −0.4330, −0.8820 \| +0.7924, −0.8865 | R₀ 7.47 cm | — | §19 | `e6c4145` |
| 154 | constants, S2-class-flat † seed 2 | −0.5426, −0.9800 \| +0.9467, −0.8113 | R₀ 8.88 cm | — | §21 | `ce427a8` |
| 155 | constants, S2-class-flat † seed 3 | −0.4097, −0.7527 \| +0.7326, −0.6060 | R₀ 8.64 cm | — | §21 | `ce427a8` |
| 156 | constants, S2-class-rough † | −0.2491, −0.9093 \| +0.8620, −0.6283 | R₀ 4.47 cm | — | §19 | `e6c4145` |
| 157 | constants, S2-class-rough-tau † | −0.2367, −0.8740 \| +0.7398, −0.2404 | R₀ 4.44 cm | — | §20 | `3229c59` |
| 158 | derived rotation rates, S2-flat † / S2-rough † state 0 | −1.414 / −1.667 | rad/s | rad/s | §4.1 | `9fa30a5` |
| 159 | §8: mean per-robot survival table, B0 / B1 ‡ / D ‡ at 0.14 R | 0.8077 / 0.8788 / 0.8621 | [0.7999,0.8153] / [0.8723,0.8851] / [0.8552,0.8687] | — | §8 | `c5203f4` |
| 160 | §8: the same at 0.27 R | 0.6164 / 0.7369 / 0.7442 | [0.6068,0.6259] / [0.7282,0.7454] / [0.7356,0.7527] | — | §8 | `c5203f4` |
| 161 | §8: the same at 0.81 R | 0.0199 / 0.1295 / 0.5084 | [0.0173,0.0228] / [0.1231,0.1362] / [0.4986,0.5182] | — | §8 | `c5203f4` |
| 162 | §8: the same at 1.35 R (perfect perception) | 0.0199 / 0.0655 / 0.3816 | [0.0173,0.0228] / [0.0608,0.0705] / [0.3721,0.3912] | — | §8 | `c5203f4` |

**Freeze lift 1 — rows 163–189.** Four experiments run against four reviewer
objections, each pre-registered before its sweep. Every row below is recomputed
by `scripts/verify_numbers.py`, and the four decision scripts it pulls from are
the single implementation of each statistic. Commits are the commit the sweep ran
at; the pre-registration hash is given in the source column because it, not the
sweep, is what makes the rule a rule.

| # | quantity | value | CI | unit | source | commit |
|---|---|---|---|---|---|---|
| 163 | **G4: best-of-three searched S = 3 † beats B0-blind at h = 1.93 s** | **18 of 25** cells (0 worse, 7 overlapping; per seed **18 / 17 / 14**) | — | held-out cells | §22, prereg `577f15a` | `ceda8b6` |
| 164 | G4: dispersion among survivors, best-of-three S = 3 † vs B0-blind | **1.41 vs 1.45** | [1.399, 1.423] vs [1.445, 1.472] | m | §22 | `ceda8b6` |
| 165 | G4′: rule (a), S3-survival_task-s2 † against B1-ternary ‡ | 13 of 25 cells (1 worse, 11 overlapping) | — | held-out cells | §22 | `ceda8b6` |
| 166 | §22: pooled mean per-robot survival at h = 1.93 s, S3-survival_task-s2 † / B1 ‡ / B0 | 0.5125 / 0.4596 / 0.3655 | [0.5081,0.5169] / [0.4553,0.4640] / [0.3613,0.3697] | — | §22 | `ceda8b6` |
| 167 | §22: rule (b), dispersion among survivors, the three survival-only rows † | 14 492 / 10 872 / 9 744 | — | m | §22 | `ceda8b6` |
| 168 | §22: runs with ≤ 5 survivors, **as a share of USABLE runs** — survival-only † / D ‡ / B1 ‡ | **0 / 0 / 0 %** vs **8.1 %** vs **11.7 %** | 2500/2500 usable vs 2476/2500 vs 1479/2500 | — | §22 | `ceda8b6` |
| 169 | §22: Pareto at r_p = 0.2 m, κ = 0 — two-axis † vs D ‡ | 0.6795 at 1.39 vs 0.7040 at 379.90 | [0.6587,0.6996] vs [0.6836,0.7236] | survival, m | §22 | `ceda8b6` |
| 170 | **A1 at n = 50**: best S = 2 / S4-terrain † / S4-warm † | 1.0412 / 1.1277 / 1.1175 | [0.9640,1.1155] / [1.0841,1.2507] / [1.0673,1.1814] | hold ratio | §23, prereg `0dd7ae1` | `1582175` |
| 171 | **A1 at n = 10, τ = 3600 s**: best S = 2 / S4-terrain † / S4-warm † | 1.1449 / 1.0490 / 1.1158 | [1.1055,1.1748] / [1.0275,1.1124] / [1.0699,1.1479] | hold ratio | §23 | `493ec46` |
| 172 | §23: the pre-registered τ contingency firing, S2-gauci reach at n = 10, θ_m = 0.9, τ = 600 s → 3600 s | 0.71 → **1.00** | [0.61,0.79] → [0.96,1.00] | — | §23 | `493ec46` |
| 173 | §23: the n = 10 margin — S4-terrain's upper bound minus the best S = 2 row's lower bound | **0.0069** | — | hold-ratio units | §23 | `493ec46` |
| 174 | **A3: paired terrain-tuning term at θ_m = 0.9**, λ = 0.05 / 0.10 / 0.20 m | **+0.0951 / +0.0818 / +0.0368** | [+0.0456,+0.1366] / [−0.0008,+0.1331] / [+0.0165,+0.0667] | m | §24, prereg `d6c40c8` | `9cc4aee` |
| 175 | §24: objective-tuning share of the anchor-to-rough gap, three λ | 95.0 / 96.9 / 94.4 | terrain share 5.0 / 3.1 / 5.6 | % | §24 | `9cc4aee` |
| 176 | **A2: matched-controller cost, as a range over three λ** | **+1.2 % to +21.4 %** | §12.1 D1 paired form; replaces the single-λ 10–20 % | % | §24 | `9cc4aee` |
| 177 | **A8: the θ_m = 0.6 crossing**, λ = 0.05 / 0.10 / 0.20 m | +0.0659 / +0.0421 / −0.0160 | [+0.0296,+0.0918] / [+0.0107,+0.0659] / [−0.0305,+0.0043] | m | §24 | `9cc4aee` |
| 178 | §24: the anchor's own hold ratio at three λ (the gap being decomposed shrinks with it) | 2.0719 / 2.1492 / 1.5186 | — | hold ratio | §24 | `9cc4aee` |
| 179 | §24: pairing check — run *i* is the same seed and initial dispersion at every λ | **600 of 600, 0 disagreements** | — | run indices | §24 | `9cc4aee` |
| 180 | **Pseudo-reality comparison 1** (terrain tax) | **ROBUST** | 10/10 same sign, 10/10 disjoint | of 10 models | §25, prereg `367ee93` | `cfa5288` |
| 181 | **Pseudo-reality comparison 2** (capability flatness) | *not established either way* | 9/10 sign, **4/10 disjoint**; the flip is model 09 at −0.0554 [−0.0879,−0.0183] | of 10 models | §25 | `cfa5288` |
| 182 | §25: is any S = 4 row **disjointly better** than S = 2 — A1 as worded | **1 of 10** (model 09); not in the reference | — | of 10 models | §25 | `cfa5288` |
| 183 | **Pseudo-reality comparison 3** (confusion through aggregation), B0 / B1 ‡ / D ‡ | ROBUST / ROBUST / ROBUST | 10/10 / 10/10 / **10/7** disjoint | of 10 models | §25 | `cfa5288` |
| 184 | **Pseudo-reality comparison 4**, r_p = 0.1 / 0.35 / 1.0 m | *not established* / ROBUST / ROBUST | **10/3** / 10/10 / 10/10 disjoint | of 10 models | §25 | `cfa5288` |
| 185 | **Pseudo-reality comparison 5** — S3 † against B1 ‡ at r_p = 1 m | **1 of 14 orderings FRAGILE** | 5/10 same sign, 7/10 disjoint, **5/10 flips**, all of them `dt = 0.05` models | of 10 models | §25 | `cfa5288` |
| 186 | §25: reach diagnostic, lowest anywhere — *reported, not thresholded* | **0.65**, S2-gauci in model 05 (reference 0.86) | — | — | §25 | `cfa5288` |
| 187 | **D10 split**: sign flips in the model-only sub-family (`dt = 0.10`) | **1 of 14 orderings** (comparison 2) | 2 further orderings flip only in the control-period half | of 14 | §25 | `0cd99a7` |
| 188 | **Phase 5c: S2-gauci reach at θ_m = 0.9, noise-free, by control period** | **0.9050 → 0.6150**, DISJOINT | [0.8723,0.9300] → [0.5664,0.6614]; S2-searched 0.9950 → 0.9825, overlapping | dt 0.10 → 0.05 | §25 | `0cd99a7` |
| 189 | Phase 5c: the same row's hold ratio, noise-free, by control period | **2.0739 → 2.9747**, DISJOINT | [1.9538,2.2019] → [2.7337,3.2093] | hold ratio | §25 | `0cd99a7` |

---

## Freeze 2

This document describes the evidence base as re-frozen at **`freeze-2`**. The
original freeze was `ce427a8`; it was lifted once, on instruction, for the four
pre-registered experiments in §§22–25 of `findings.md`, and closed again.

* **Evidence base**: `findings.md` §1–§25, `literature-corrections.md` #1–#17,
  `validation.md`, and the four pre-registrations under `docs/preregistration/`.
* **§13 rows 163–189** are new. Rows 13, 14, 23 and 24 carry corrected values
  (F1, F2 — no claim changes); row 31's interval is restated Wilson per §12.1 D0;
  rows 56–58 keep their values and carry a provenance note (F3).
* **Verification at this freeze**: `scripts/check_section13.py` reports **114
  MATCH, 0 MISMATCH**, with three rows in the documented F3 category, six
  recomputing a statistic §13 retired, one documented in §12.1 and one re-seeded
  resample. `scripts/verify_determinism.py` is IDENTICAL. 128 Rust tests, 32
  harness tests.
* **`docs/paper-source.json` is generated** from §13 of this file by
  `scripts/sync_paper_source_json.py`; the markdown is the authority.

## What could not be sourced from the repository

Everything above is taken from `docs/findings.md` §1–§21,
`docs/literature-corrections.md` #1–#15, `docs/validation.md`, the ADRs, the
sweep and search configs, the results files, the figure scripts and the test
suite; where a number is quoted it was checked against the results file that
produced it, and the three places where a document and a file disagree are in §12
rather than silently reconciled. Five things a paper will want are **not** in the
repository and must be supplied by the author or dropped: a bibliographic entry
for **Holling's disc equation**, which correction #7 uses by concept only; a
bibliographic entry for **Graham & Sloane**, whose normalised-second-moment
convention the dispersion metric follows; the **specific insider-adversary
references** the build doc gestures at ("Byzantine robots in collective
decision-making; FL poisoning in ROS2 swarms, 2026"); the **check of absolute
dispersion against Gauci's published figures**, which the week-1 gate left open
and which makes every absolute dispersion value in this paper provisional; and
any **verification of the twelve reading-list references** beyond Gauci 2014,
Steinberg & Solovey 2024 and Daymude et al. 2021 — the venues and years are as
the build doc recorded them and were not independently checked here. Two further
absences are structural rather than bibliographic: **no Tier 2 (ARGoS) or hardware
result exists**, so nothing in this paper speaks to the reality gap; and **the
pre-registered Friedman-with-post-hoc comparison and the single pre-registered
threshold `T` were never run or fixed**, which is a protocol deviation the paper
must disclose rather than paper over.
