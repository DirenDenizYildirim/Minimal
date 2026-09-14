# Pre-registration — capability flatness at n ∈ {10, 50} (freeze lift 1, experiment 2)

Filled from `template.md` and committed **before** the sweep runs. The commit hash
of this file is what makes the rule below pre-registered; `docs/findings.md` §23
will cite it.

## Question

A1 says: **no S = 4 controller better than the searched S = 2 one was found at
equal budget** — a terrain bit does not buy back the peak. Every measurement
behind it is at n = 20. Does it hold away from n = 20?

This is an evaluation, not a search. **No row is re-searched**, deliberately: the
question is whether the *existing* controllers' ordering survives a change of
swarm size, and re-searching at each n would answer a different question (whether
a controller tuned for that n does better) while spending an order of magnitude
more compute. The limitation this leaves is stated below and must be carried into
the paper.

## Task and threshold

* Behaviour: aggregation.
* Primary metric: **hold ratio** — dispersion at θ_m = 0.9 divided by the *same
  run's* dispersion on flat ground, **paired by run index**, reported as the median
  of the per-run ratios with a 95% percentile-bootstrap CI. This is §12.1 D1's
  single definition, the one the paper is settling on; the retired
  ratio-of-medians form is not used here.
* Threshold `T`, direction: lower is better. The rule below is stated on interval
  disjointness rather than a bar, which is what a "no row is better" claim needs.
* Secondary metrics, reported but not thresholded: absolute final dispersion with
  intervals at both θ_m; **reach** (share of runs ever in a single cluster) with a
  **Wilson** interval, because reach is a proportion and its median is 1 whenever
  the majority succeed.
* Cluster link distance: 3.0 body radii.

## Capability rows

Constants copied **verbatim** from the configs that already carry them, so this
sweep introduces no new controller. The terrain-bit definition is copied verbatim
too: `sensor.encoding = "binary_with_terrain"` with the threshold left at its
default, `θ_m × MEDIAN_ABS` = `θ_m × 0.3476`, which keeps the bit roughly 50/50
and therefore informative.

| Row | S | M | A | K | Provenance | Free constants | Source of the constants |
|---|---|---|---|---|---|---|---|
| S2-gauci | 2 | 0 | no | 0 | enumerated | 4 | `gauci_baseline.toml` |
| S2-class-flat-s1 † | 2 | 0 | no | 0 | optimiser_found | 4 | `terrain_class_eval.toml` / §19 |
| S2-class-flat-s2 † | 2 | 0 | no | 0 | optimiser_found | 4 | `phase0_seeds.toml` / §21 |
| S2-class-flat-s3 † | 2 | 0 | no | 0 | optimiser_found | 4 | `phase0_seeds.toml` / §21 |
| S2-searched † | 2 | 0 | no | 0 | optimiser_found | 4 | `terrain_h3_capability.toml` |
| S4-terrain † | 4 | 0 | no | 0 | optimiser_found | 8 | `terrain_h3_capability.toml` |
| S4-warm † | 4 | 0 | no | 0 | optimiser_found | 8 | `terrain_warm_s4.toml` |

Only S2-gauci is a tight minimum. Every other row is an **upper bound** and carries
†. Two S = 4 rows are included rather than one because §10's warm start is the
answer to the equal-budget objection: it began at `[S2-searched | S2-searched]`, an
S = 4 table that ignores its own bit, so it had access to the S = 2 optimum.

**The three class-flat seeds are the baseline, best-of-three per cell**, not
S2-class-flat-s1 alone. §21's branch (b) fired — the seeds scatter, R₀ spanning
16.9% against a pre-registered 10% rule — and retired the single named baseline.
Comparing an S = 4 row against the weakest of three draws would be the same
mistake §21 exists to prevent.

## Environment grid

| Dial | Values | Notes |
|---|---|---|
| `swarm.n` | 10, 50 | n = 20 is the existing record and is **not** re-run |
| `terrain.friction_amplitude` θ_m | 0.0, 0.9 | 0.0 is the paired flat-ground baseline, not a data point |
| `terrain.correlation_length` λ | 0.10 m | fixed — this experiment varies n, not λ; experiment 3 varies λ |
| `sim.duration` τ | 600 s, and 3600 s at n = 10 **only if** reach < 0.8 there at 600 s | see below |

Fixed: `swarm.init.coverage = 0.05`, so the start radius is **derived** per n and
initial density is constant — **0.523 m at n = 10** and **1.170 m at n = 50**,
against 0.740 m at n = 20. Hard-coding a radius would confound swarm size with
initial density, which is the whole reason the coverage rule exists. Also fixed:
slope 0, no occlusion, no actuation noise, `dt = 0.1`.

**The τ = 3600 s contingency is pre-registered, not discretionary.** Small swarms
are slow: §14 showed reach at the largest start radius rising from 0.46 to 1.00
between τ = 600 s and τ = 3600 s, and §20 showed a truncated objective producing a
diagnosis that was simply wrong. The trigger is fixed here: **if any row's reach at
n = 10, θ_m = 0.9, τ = 600 s is below 0.8, the whole n = 10 block is re-run at
τ = 3600 s and both trial lengths are reported.** A hold ratio measured where the
swarm has not finished aggregating is a measurement of the clock.

## Design

* Runs per cell: **100**. Config: `configs/sweeps/terrain_capability_n.toml`.
* Seed: `20260904`, one base seed across every cell, so run *i* is the same
  placement and the same traction field in every row — which is what makes the
  paired ratio legitimate rather than a difference of two independent samples.
* Statistics: paired hold ratios with bootstrap CIs; absolute dispersion with
  bootstrap CIs; reach with Wilson intervals. Every number enters the record
  through `swarm_harness.stats` and is added as an `item(...)` to
  `scripts/verify_numbers.py`.
* Search budget: **none — nothing is searched here.** The budgets that produced
  the rows stand as recorded: 600 × 12 for S2-searched, S4-terrain and S4-warm;
  1200 × 12 for the three class-flat seeds.

## Predictions

* **H1.** A1 holds at both n. The mechanism §7 identified is that re-searching the
  four constants shrinks R₀ away from the worst λ/R₀, and R₀ is a property of the
  controller, not of the swarm — so the ordering should not care about n.
* **H2.** The *absolute* hold ratios fall with n at both θ_m, because a larger
  swarm aggregates more tightly (§validation 1: 1.68 at n = 10, 1.43 at n = 20,
  1.20 at n = 50 on flat ground) and terrain has less room to spoil a tighter
  cluster. H2 is about magnitude and does not bear on A1, which is about ordering.
* **H3.** n = 10 will need τ = 3600 s and n = 50 will not.

## Pre-registered decision rule

**Per n, reported separately. The two swarm sizes are not pooled** — pooling would
let a result at one n carry a null at the other, and "A1 holds at n = 10 and fails
at n = 50" is a publishable answer that pooling would hide.

* **A1 holds at that n** if **no S = 4 row's hold ratio at θ_m = 0.9 is below the
  best S = 2 row's with disjoint intervals.** "Best S = 2 row" is the best-of-three
  class-flat baseline together with S2-searched, taken per cell.
* **A1 fails at that n** if either S = 4 row is disjointly below every S = 2 row.
  That is the outcome that would move the claim, and it is named here so it cannot
  be explained away later.
* **Neither** — an S = 4 row disjointly below some S = 2 rows but not all — is
  reported as such, with the rows named. It is not evidence for A1 and must not be
  written as if it were.
* If the τ = 3600 s contingency fires at n = 10, the rule is evaluated at
  **τ = 3600 s** there and the τ = 600 s numbers are reported alongside as the
  truncated view.

## Budget

`--dry-run` before running, reported at the **× 2.1** correction the Phase 0
review set. 7 rows × 2 n × 2 θ_m × 100 runs = 2 800 trials at τ = 600 s, plus
1 400 more if the n = 10 block re-runs at τ = 3600 s. Stop and report rather than
reduce runs per cell if the revised **60 core-hour** plan ceiling is threatened.

## Deviations

Anything that changed after registration, and why. Append; do not edit above.

*(none yet)*
