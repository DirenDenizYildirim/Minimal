# Pre-registration — a *searched* S = 3 pursuer row (freeze lift 1, experiment 1)

Filled from `template.md` and committed **before** either search runs. The commit
hash of this file is what makes the rules below pre-registered rather than chosen
after seeing the result; `docs/findings.md` §22 will cite it.

## Question

Is the survival advantage of S = 3 — telling a pursuer from a neighbour — a
property of the **capability**, or of the hand-designed rows B1–B3? Every S = 3
row in the record is ‡, so claim G4 is graded SUGGESTED. A searched row cannot
make it tight, but it can make it a measurement: an upper bound, stated with †.

## Task and threshold

* Behaviour: survival under an active pursuer, with aggregation as the base task.
* Primary metric: **mean per-robot survival at τ**, captured robots counting as 0,
  pooled over the runs in a cell and given a **Wilson** interval. This is the
  statistic `scripts/recompute_paired_and_survival.py` already uses and the one
  §12.1 D0 moved the record to; a median of a per-run proportion at n = 20 can
  only land on a twentieth and reports the grid rather than the uncertainty.
* Threshold `T`, direction: the decision rule below is stated on interval
  disjointness rather than on a single bar, but it carries two fixed numbers and
  they are the thresholds: **≥ 12 of 25 held-out cells** at h = 1.93 s must be
  disjointly better, and dispersion among survivors must stay **< 3.0**. Both are
  set here, before any search runs.
* Secondary metrics, reported but not thresholded: dispersion among survivors
  (survivors only, ≥ 3 of them, else undefined and reported as such);
  `time_to_wipeout` where survival saturates; the state-0 turn radius R₀; the
  reported-versus-re-scored training objective (the winner's-curse gap).
* Cluster link distance: 3.0 body radii, the repository default.

## Capability rows

| Row | S | M | A | K | Provenance | Free constants | Enumerable at Gauci's resolution? |
|---|---|---|---|---|---|---|---|
| B0-blind | 2 | 0 | no | 0 | enumerated (Gauci) | 4 | yes — it is the enumerated row |
| B1-ternary ‡ | 3 | 0 | no | 0 | hand_designed | 6 | no: 20⁶ ≈ 6.4 × 10⁷ at Gauci's resolution |
| D-dispersive ‡ | 3 | 0 | no | 0 | hand_designed | 6 | no |
| A1, A2, A3 † | 3 | 0 | no | 0 | optimiser_found, objective `survival`, seeds 1/2/3 | 6 | no |
| B1s, B2s, B3s † | 3 | 0 | no | 0 | optimiser_found, objective `survival_task`, seeds 1/2/3 | 6 | no |

The six searched rows are **upper bounds**. sep-CMA-ES is not exhaustive and its
diagonal covariance makes it a weaker searcher than full CMA-ES, which loosens
the bound and never falsely tightens it. This must be said in the abstract and on
every figure, with †.

## Environment grid

**Training class — six conditions, crossed:**

| Dial | Values | Notes |
|---|---|---|
| `pursuer.range` | 0.2, 0.35, 0.6 m | 0.27 R, 0.47 R, 0.81 R at R = 0.74 m |
| `pursuer.confusion` | 0.5, 2.5 | spans the regime where κ buys survival |

Held fixed in training: `pursuer.handling_time = 1.93` (5× the 0.385 s the
pursuer needs to travel between touching neighbours, so handling dominates and
dilution has room to act), `pursuer.speed_ratio = 1.5`,
`pursuer.confusion_radius = 0.5`, `sim.duration = 120.0`, `swarm.n = 20`,
`swarm.init.coverage = 0.05` (start radius 0.740 m, derived not hard-coded),
`sensor.encoding = "ternary"`, `dt = 0.1`, flat ground, no occlusion, no noise.

**Why the class is where it is.** r_p = 0.1 m is excluded because every row keeps
17–18 of 20 there and the cell cannot discriminate; r_p = 1.0 m is excluded
because it is the perfect-perception corner (1.35 R — the pursuer sees the whole
starting swarm from anywhere in it) and was measured identical to r_p = ∞. κ = 0
is excluded because the blind row is wiped out there at every range beyond 0.1 m,
and a condition that scores 0 for a whole neighbourhood of the search space
carries no gradient. The evaluation grid keeps all of them; the *training* class
is the part of it that can distinguish candidates.

**Evaluation grid — the full `pursuer_dispersive.toml` grid, held out:**

| Dial | Values | Notes |
|---|---|---|
| `pursuer.range` | 0.1, 0.2, 0.35, 0.6, 1.0 m | 0.14, 0.27, 0.47, 0.81, 1.35 R |
| `pursuer.confusion` | 0.0, 0.5, 1.0, 2.5, 5.0 | |
| `pursuer.handling_time` | 0.39, 1.93 s | |

50 cells × 9 rows × 100 runs = 45 000 trials, plus the three Pareto cells of
`pursuer_pareto.toml` — (r_p, κ) = (0.2, 0.0), (0.35, 3.0), (1.0, 3.0) at
h = 1.93 s — × 9 rows × 100 runs. Config: `configs/sweeps/pursuer_searched_s3.toml`.
B0-blind, B1-ternary ‡ and D-dispersive ‡ are evaluated **in the same sweep** so
every comparison sits on identical seeds and pairs by run index.

## Design

* Runs per cell: **100**, evaluation seed `20260904`, disjoint from training.
* Training seed base: **930000**. Optimiser seeds **1, 2 and 3**, varying `--seed`
  only and holding the training base fixed — which is exactly how §21's seed study
  separated optimiser variability from a different draw of training arenas. The
  CLI already separates the two, so 931000 / 932000 are **not** used.
* Optimiser: sep-CMA-ES (Ros & Hansen 2008), diagonal covariance, box-constrained
  to [−1, 1] with a 10× squared repair penalty.
* Budget: **1200 evaluations × 12 runs = 14 400 runs per search**, the *doubled*
  budget §19 established, because the class has six conditions and 12 runs over 6
  conditions is 2 runs per condition per evaluation. Stated here so the comparison
  against the single-condition rows is quotable rather than implied.
* Initial point, for **every** search, **verbatim from
  `configs/sweeps/pursuer_dispersive.toml`'s B1-ternary row**:

  ```
  [-0.7, -1.0,   1.0, -1.0,   -1.0, -1.0]
   state 0        state 1      state 2
   (nothing)      (robot)      (pursuer)
  ```

  The search therefore starts *at the hand-designed row* and can only be asked one
  question: is there better? A null result then means "no improvement found from
  this known-good point", which is a sharper statement than "nothing found".
* Statistics: mean per-robot survival with Wilson intervals; medians with 95%
  percentile-bootstrap CIs for dispersion; paired by run index where two rows are
  compared on the same cell. Every number enters the record through
  `swarm_harness.stats` or `scripts/recompute_paired_and_survival.py` and is added
  as an `item(...)` to `scripts/verify_numbers.py`.
* Honest re-score: every returned controller is re-scored at **100 runs per
  training condition** on held-out seeds, and the reported-minus-re-scored gap is
  recorded per row. §20 and §21 both show the returned training objective is the
  minimum of a noisy sample.

### The two objectives, defined before they are implemented

Neither exists in `swarm search` today. `crates/swarm-cli/src/search.rs` currently
hard-codes the objective to the median `final_dispersion`; a probe confirms the
other two prerequisites already hold — a `kind = "table"` controller with
`sensor.encoding = "ternary"` searches over six constants, and a `[pursuer]` block
is live during the search (a 5-run probe at r_p = 0.35, κ = 2.5 gives 0–8 captures
per run). Both objectives below are added behind `--objective`, whose **default is
the existing median-dispersion behaviour**, so every existing search is bit-neutral;
`cargo test` and `scripts/verify_determinism.py` are run before and after and must
be identical.

* `--objective survival` — mean per-robot survival at τ, captured robots counting
  as 0, pooled over the trials of a condition. Higher is better.
* `--objective survival_task` — the geometric mean of that survival and
  `1 / dispersion_among_survivors`, both per condition, so the search cannot buy
  survival by abandoning the task. Dispersion among survivors is the existing
  dispersion metric computed on the surviving robots only. **If fewer than 3
  robots survive the task term is undefined and the condition scores 0** — one or
  zero survivors would otherwise score a perfect aggregation for a swarm that has
  been wiped out.
* Class aggregation for both: the **geometric mean of the per-condition values**,
  as for the dispersion objective. The guard against zero is deliberate and is not
  a floor: each per-condition value is a proportion, and **if it is 0 in any
  condition the geometric mean is 0**. A candidate that wipes out anywhere scores
  0, and that is the honest answer.
* Sign convention, pinned so it cannot drift: the optimiser minimises `−score`;
  the `best_training_objective` recorded in the JSON is the **score itself, higher
  better**, and the JSON's `objective` string states the direction.

### Search provenance, required (finding F3)

Phase 0 found the four single-condition searches non-regenerable: no section
records their optimiser seed, and re-running the recorded protocol returns
different constants. Before any search in this experiment runs, `swarm search`
must record in its output JSON — additively, with tests, and bit-neutral for
existing runs:

* the optimiser seed, the training seed base and the budget (already recorded);
* the **git hash** of the working tree it ran at;
* a **hash of the fully-resolved base config**, so a later edit to the config
  cannot silently invalidate the row.

Every search in this experiment uses that build. This is the disclosure F3 turned
into a requirement, not a nicety.

## Predictions

State them before looking. A hypothesis that could not have failed is not one.

* **H1.** A `survival_task` search will find a row that beats B1-ternary ‡ on
  survival somewhere, because B1 is a hand-written guess in a six-constant space
  and §5 already showed a hand-written S = 5 row (B2) scoring *below* S = 3. What
  is genuinely open is whether it beats B1 in enough of the grid to move G4, and
  the rule below fixes "enough" at 12 of 25 before the answer is visible.
* **H2.** A `survival`-only search will drift toward D-dispersive: a long state-0
  arc, no aggregation, high survival. §8 established that D survives well while
  abandoning the task, and nothing in the `survival` objective penalises that. If
  H2 holds it is a result in its own right about objective design, not a failure
  of the experiment.
* **H3.** The three optimiser seeds will scatter by more than the 10% R₀ rule §21
  pre-registered, because a pursuer class is noisier than a flat-ground one and
  §21 already found 16.9% on the easier problem.

## Pre-registered decision rule

Evaluated on the held-out grid above, after the honest re-score.

* **(a) G4 is upgraded** — the S = 3 advantage becomes a measured upper bound,
  stated with † — if a **Search-B (`survival_task`) row beats B1-ternary ‡ on mean
  per-robot survival with disjoint Wilson intervals in ≥ 12 of the 25 cells at
  h = 1.93 s**, *while* keeping **dispersion among survivors < 3.0**. Both
  conditions must hold for the same row.
* **(b) Reported as a finding in its own right** — "a survival-only search
  abandons the task", which supports the two-axis (B5) framing — if the
  **Search-A (`survival`) rows converge toward D-dispersive**: state-0 arc
  **> 50 cm** and dispersion among survivors **> 10**.
* **(c) G4 stays SUGGESTED with its existing hedge** if neither fires. The
  searched rows are then reported as further evidence that the hand-designed rows
  are not far from what a class search of this budget finds — which is a weaker
  claim than (a) and must not be written as if it were (a).
* **Seed spread**, reported whichever branch fires: the spread of state-0 R₀
  across the three optimiser seeds, as a percentage of their mean, against the
  **10% agreement rule** §21 pre-registered. If it exceeds 10%, the baseline for
  this experiment is **best-of-three † per cell**, as §21's branch (b) established,
  and every downstream number is stated against best-of-three.
* Rows (a) and (b) are not exclusive: a `survival_task` row may qualify under (a)
  while the `survival` rows qualify under (b), and both are then reported.

## Budget

`--dry-run` before running, reported at the **× 2.1** correction the Phase 0
review set on the throughput model. Six searches at 14 400 runs (n = 20,
τ = 120 s) plus 45 000 + 2 700 evaluation trials. If any single experiment exceeds
2 × 10⁶ robot-timesteps × 100, or the plan exceeds the revised **60 core-hour**
ceiling, stop and report rather than reducing runs per cell.

## Deviations

Anything that changed after registration, and why. Append; do not edit above.

**D1 — how `survival_task`'s three-survivor guard was operationalised**, recorded
before the searches ran. The registration says "if fewer than 3 survive, the task
term is undefined and the condition scores 0", which reads per *run* while the
objective is defined per *condition*. Implemented as: a run with fewer than three
survivors contributes no task term, the condition's task term is the median over
the runs that do clear the bar, and a condition in which **no** run clears it
scores 0. That preserves the guard's purpose exactly — a swarm reduced to two
robots sitting on each other must not score a perfect dispersion — without
discarding a condition because one of its two training runs went badly.
`crates/swarm-cli/src/search.rs` carries the same wording, and
`a_run_with_too_few_survivors_contributes_no_task_term` pins it.

**D2 — what the searches measured, recorded after they ran and before the
evaluation was read.** All six searches recorded a clean git hash and config
hash, so the F3 requirement above was live for its first use. Optimiser seeds 1,
2 and 3 with the training base held at 930000, as registered.

**D3 — G4 is split in two, on review, after the rule fired.** The rule itself is
NOT changed and was not re-run: `S3-survival_task-s2` beat B1-ternary ‡ in 13 of
25 cells against a threshold of 12, and that is reported as a pass. What changed
is which claim the result feeds. The rule compared against B1 because B1 was the
best S = 3 row in existence; now that a searched row exists, the *capability*
question — S = 3 against S = 2 — is properly asked against **B0-blind**, and that
comparison is a different and much stronger one (18 of 25, 0 losses). So:

* **G4**, the capability claim, is stated against B0 and graded on the B0
  comparison.
* **G4′**, secondary and regime-specific, is stated against B1 and carries the
  13-of-25, one-seed-of-three margin as an explicit hedge.

This is a re-attribution of an unchanged measurement, not a re-run against a
moved bar, and it is recorded here so that distinction is on the record rather
than in a reviewer's inference. Both comparisons come from the same sweep and
the same seeds; no new simulation was run for either.
