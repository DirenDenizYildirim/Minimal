# Pre-registration — pseudo-reality robustness check (freeze lift 1, experiment 4)

Filled from `template.md` and committed **before** the models are sampled or any
sweep runs. The commit hash of this file is what makes the sampling seed, the
model family and the rule below pre-registered; `docs/findings.md` §25 will cite
it.

## Question

Every result in this paper was obtained on one simulator with one set of
modelling choices. Do the headline **orderings** survive evaluation on models
other than the one they were obtained on?

This follows Ligot & Birattari (2020, *Swarm Intelligence* 14), who evaluate
control software on **pseudo-realities** sampled around the design model and read
robustness from whether orderings hold. It is the cheapest available answer to
"purpose-built simulator, single model, no reality-gap check", and it is
explicitly **not** a reality-gap study: no hardware, no ARGoS, no second
simulator. §12.3 already records that none of those exist, and this experiment
does not change that. What it can say is whether a result is an artefact of one
point in model space or survives a neighbourhood of it.

## Task and threshold

* Behaviour: aggregation, and survival under a pursuer.
* Primary metric: **per comparison, the statistic that comparison already uses** —
  listed in the table below. Nothing new is invented; the point is to re-measure
  existing statistics on perturbed models.
* Threshold `T`, direction: the rule turns on **sign agreement and interval
  disjointness across models**, counted. The two counts are fixed here: **≥ 9 of 10
  same sign** and **≥ 7 of 10 disjoint** for robust, **≥ 3 of 10 sign flips** for
  fragile.
* Secondary, reported but not thresholded: which sampled parameter, if any, is
  associated with the flips — **as a table of the flipping models' parameter
  values, not as a regression.** Ten points cannot support a regression over six
  parameters, and fitting one would manufacture a mechanism the design cannot see.
* Cluster link distance: 3.0 body radii, unperturbed. It is a parameter of the
  *metric*, not of the model, and perturbing it would change what is being
  measured rather than what is being simulated.

## The model family

**K = 10 models**, each parameter drawn **uniformly and independently**, from a
**fixed sampling seed recorded here before the draw: `20260910`**, consumed by
`numpy.random.default_rng(20260910)` in the order the table lists.

| parameter | range | default | note |
|---|---|---|---|
| `noise.wheel_noise` | [0.00, 0.05] | 0.00 | per ADR 0004 this is a dial, off by default, and measured mildly harmful at n = 20 |
| `occlusion.fn_rate` | [0.00, 0.10] | 0.00 | i.i.d. dropout, `occlusion.correlation_amplitude` held at 0 |
| `occlusion.fp_rate` | [0.00, 0.02] | 0.00 | |
| `sim.collision_iterations` | {8, 16, 32} | 32 | discrete, drawn uniformly |
| `sim.contact_tolerance` | [0.5×, 2×] × 1e-5 = [5e-6, 2e-5] | 1e-5 | |
| `sim.dt` | {0.05, 0.10} | 0.10 | discrete; the simulator is timestep-independent by test, and this checks it under noise too |

Written to `configs/pseudo_reality/model_01.toml` … `model_10.toml` by a script
committed under `scripts/`, so the draw is reproducible from the seed rather than
transcribed. **Model 00 is the unperturbed reference** and is the existing
baseline config, included in every comparison as the reference point and marked as
such on the figure. The ten sampled models are tabulated in the findings section
with their parameter values.

**What this family is and is not.** It perturbs *implementation* choices —
actuation noise, sensor dropout, contact solver effort, timestep — around the
design point. It does not perturb the *physics being modelled*: the kinematics,
the traction model, the pursuer's lock-on law and the sensor geometry are the
same in every model. A result robust across this family is robust to how carefully
the simulator is integrated and how noisy its sensors are, not to whether the
model is right. That distinction belongs in the paper's wording and is the main
way this experiment can be over-claimed.

## Capability rows and comparisons

Every comparison is evaluated on **all eleven models** (00 plus 01–10), at **100
runs per cell**, with **seeds paired within a model** so the two sides of each
comparison see the same placements.

| # | comparison | cells | statistic |
|---|---|---|---|
| 1 | terrain tax: S2-gauci vs best-of-three S2-class-flat | θ_m ∈ {0, 0.9}, λ = 0.10 m, n = 20, R = 0.74 m | paired hold ratio for each row, and the **paired difference between them at θ_m = 0.9** |
| 2 | capability flatness: S2-searched † vs S4-terrain † | the worst cell (λ = 0.10 m, θ_m = 0.9, n = 20) | paired hold-ratio **difference** |
| 3 | confusion through aggregation: B0-blind, B1-ternary ‡, D-dispersive ‡ | r_p = 0.35 m, κ ∈ {0, 5}, h = 1.93 s | **κ-response ratio** per row (mean per-robot survival at κ = 5 over κ = 0) |
| 4 | matched-pair ordering: B1-ternary ‡ vs D-dispersive ‡ | r_p ∈ {0.1, 0.35, 1.0} m, pooled over κ, h = 1.93 s | **sign and disjointness** of the mean per-robot survival difference at each r_p |
| 5 | *conditional* — the Phase 2 Search-B row vs B1-ternary ‡ | the same cells as comparison 4 | as comparison 4 |

**Comparison 5 runs only if Phase 2's rule (a) fired.** If it did not, there is no
searched row whose ordering is worth testing and the comparison is dropped, which
is recorded rather than quietly omitted.

Comparison 1 uses **best-of-three S2-class-flat per cell**, per §21's branch (b),
not the seed-1 row alone.

Survival statistics are **mean per-robot with Wilson intervals** throughout
(§12.1 D0), computed by `scripts/recompute_paired_and_survival.py` extended
additively to the new files.

## Design

* Runs per cell: **100**. Evaluation seed `20260904`, one base seed per model, so
  runs pair within a model. Runs are **not** paired *across* models: `dt` and
  `collision_iterations` differ between models, so the same seed does not produce
  the same trajectory and pretending otherwise would be false pairing.
* Config: `configs/sweeps/pseudo_reality.toml` if the sweep machinery supports a
  file-valued axis; otherwise one config per model generated by the same committed
  script that samples them. Which of the two was used is recorded in the findings.
* Statistics: as each comparison's own section already uses. Every number enters
  through `swarm_harness.stats` or `recompute_paired_and_survival.py` and is added
  as an `item(...)` to `scripts/verify_numbers.py`.
* Search budget: **none — nothing is searched here.**
* Figure: `harness/figures_pseudo_reality.py`, one panel per comparison, models on
  the x axis, the statistic with its interval on the y axis, the reference model
  marked, and the zero or one line drawn.

## Predictions

* **H1.** Comparisons 1 and 2 are robust. Both are large, repeatedly measured
  effects (hold ratios 2.149 against 1.099; S4 disjointly worse than S2) and none
  of the perturbed parameters touches the traction model that produces them.
* **H2.** Comparison 3 is robust in sign but its *magnitudes* move most under
  `occlusion.fn_rate`, because dropout degrades the very neighbour-sensing that
  aggregation-driven dilution depends on, and B0-blind has no other channel.
* **H3.** Comparison 4 is the one at risk. §8's matched pair crosses **between
  0.27 R and 0.47 R**, so at r_p = 0.35 m (0.47 R) the two rows are near the
  crossing and a small perturbation can flip the sign there while leaving 0.14 R
  and 1.35 R alone. If exactly that happens it is a **located** fragility, not a
  failure of S11 — S11 already states the crossing — and must be reported that way.

## Pre-registered decision rule

**Per comparison. No pooling across models, and no pooling across comparisons.**

* **Robust** if the ordering has the **same sign in ≥ 9 of the 10 sampled models**
  **and** **disjoint intervals in ≥ 7 of the 10**.
* **Fragile** if the sign **flips in ≥ 3 of the 10**.
* **Neither** — anything between — is reported as **"not established either way"**
  with both counts given. It is not evidence of robustness and must not be written
  as if it were. This is the branch a reviewer is most likely to be handed, and
  naming it now is what stops it being rounded up later.
* **Both counts are reported for every comparison**, whichever branch fires,
  including the reference model's value alongside so the reader can see whether
  the sampled models straddle it.
* **Flip attribution**: if any comparison is fragile, the flipping models' six
  parameter values are tabulated next to the non-flipping ones. **No regression,
  no significance test, no claim of a mechanism** — ten models over six parameters
  cannot support one, and the table is offered as a lead for future work, not as a
  finding.
* A fragile result **does not retract** the underlying claim. It bounds it: the
  claim holds at the design model, which is where it was measured and stated, and
  the finding is that it does not hold across this neighbourhood. The claims
  register entry gains that qualifier rather than losing its grade.

## Budget

`--dry-run` before running, reported at the **× 2.1** correction the Phase 0
review set. Roughly 11 models × (comparisons 1–2 at τ = 600 s, comparisons 3–5 at
τ = 120 s); the `dt = 0.05` models cost twice their `dt = 0.10` counterparts and
that is in the dry-run figure, not estimated around. Stop and report rather than
reduce runs per cell if the revised **60 core-hour** plan ceiling is threatened.

## Deviations

Anything that changed after registration, and why. Append; do not edit above.

**D1 — comparison 5 is now defined**, since experiment 1's rule (a) fired. It was
registered conditionally ("if Phase 2's rule (a) fired: that row vs B1 at the same
cells") and is now:

> **best-of-three searched S = 3 †** against **B0-blind** *and* against
> **B1-ternary ‡**, at comparison 4's cells: r_p ∈ {0.1, 0.35, 1.0} m, pooled over
> κ, h = 1.93 s. Statistic and rule as comparison 4 — sign and disjointness of the
> mean per-robot survival difference at each r_p.

Two references rather than one because experiment 1 split G4 in two (see
`searched-s3-pursuer.md` D3): the comparison against B0 is the capability claim
that goes in the abstract, and the comparison against B1 is the regime-specific
one. A robustness check on the first without the second would leave the weaker
claim untested and the stronger one looking like the only claim made.

Best-of-three is **per cell**, per §21's branch (b), which experiment 1's seed
spread (166%) put firmly in force.

**D2 — the Pareto figure gains the survival-only rows.** `figures_pareto.py`
draws §12's figure from `pursuer_pareto.jsonl` and is left alone; experiment 1's
own Pareto figure shows **all four kinds of row** on one pair of axes —
hand-designed aggregating (B0, B1 ‡), hand-designed dispersive (D ‡), searched
two-axis (`survival_task` †) and searched survival-only (`survival` †) — with the
last labelled as survival-only searches. The two-axis story is only complete with
all four: it is the searched survival-only rows that show the trade-off is not an
artefact of one hand-designed corner.
**D3 — comparison 4's κ grid is {0, 5}, not `pursuer_dispersive.toml`'s five
values.** The registration fixed comparison 3 at κ ∈ {0, 5} and said comparison 4
was "pooled over κ" without naming the grid. It is pooled over the two values
comparison 3 already requires. That keeps the pursuit sweep at 36 cells per model
rather than 90 — 3 686 Mrts total instead of about 7 400 — and it pools the two
extremes of the confusion dial rather than a middle that would dilute them, which
is if anything a harder test of an ordering than the full grid. Recorded here
rather than taken silently, because "pooled over κ" could have been read as all
five and a reader must not have to guess which.

**D4 — the file-valued axis does not exist, so the registered fallback runs.** A
sweep's `base` is a single path resolved once (`swarm-cli/src/main.rs`,
`base_path`) and an axis carries values for one config path, so a whole model
cannot be an axis value. Per the registration's own "otherwise" clause, the
family is generated as one config per model by
`scripts/build_pseudo_reality_configs.py`: ten model base configs
(`configs/pseudo_reality/model_01.toml` … `model_10.toml`, each
`gauci_baseline.toml` with exactly the six sampled parameters substituted and
every substituted line marked) plus one aggregation and one pursuit sweep config
per model, eleven of each including the unperturbed reference. **Model 00 has no
base file of its own** and points at `gauci_baseline.toml` directly: a copy of the
baseline that could drift from the baseline is worse than no copy. The generator
has a `--check` mode that fails if any generated file is stale, and the driver
runs it before the sweeps.

**D5 — comparison 2 stays at n = 20**, on review after experiment 2. That is the
only n at which A1 is graded SUPPORTED; at n ∈ {10, 50} the S = 4 candidates are
transferred rather than searched, so a robustness check there would be testing the
robustness of a claim the record does not make. No other comparison changes.

**D6 — the RNG stream is consumed model-major.** "Each parameter drawn uniformly
and independently … in the order the table lists" admits two readings: six draws
per model for ten models, or ten draws per parameter. The generator takes the
first, which is the more natural reading of "in the order the table lists" and is
now fixed in code, so the family is reproducible from the seed under either
reading of the sentence. The draw is tabulated in the findings section with all
sixty values.
**D7 — how the rule applies to a comparison that names several cells.** Written
before any Phase 5 result was computed. Comparisons 3, 4 and 5 each name more
than one ordering: comparison 3 has a κ-response ratio for each of three rows,
comparison 4 a B1-versus-D difference at each of three r_p, and comparison 5 the
searched row against two references at each of three r_p. The registration says
"per comparison, no pooling", which fixes that models are never pooled but does
not say what to do with several orderings inside one comparison.

The rule is applied to **each named ordering separately** — the atomic unit that
has a sign — and every one is reported with both counts. A comparison is called
robust only if **every** ordering in it is robust, and fragile if **any** is
fragile; anything else is "not established either way" for the comparison, with
the per-ordering verdicts given so the reader can see which cell carried it. This
is the conservative reading: taking the best ordering in a comparison, or
averaging them, would let a robust cell hide a fragile one, and H3 predicts
exactly such a split for comparison 4 at r_p = 0.35 m.

For comparison 3 the "sign" of a κ-response *ratio* is whether it exceeds 1 —
confusion buys survival or it does not — and "disjoint" means the κ = 5 and κ = 0
Wilson intervals do not overlap. For the differences in comparisons 1, 2, 4 and 5
the sign is the sign of the difference and "disjoint" means the two sides'
intervals do not overlap.
**D8 — amendment: the diagnosed cause is fixed and comparisons 3–5 are re-run on
the five `dt = 0.05` models.** Written after the registered rule had fired and
been recorded, and it does not touch that result: **§25 keeps the original
verdicts, unedited** — comparison 5 FRAGILE under the registered model family, on
the model the experiment was registered against. What follows is a second,
clearly separated question.

*Why.* The rule's flip table separated exactly on the timestep — 5 of 5 flips at
`dt = 0.05`, 0 of 5 at `dt = 0.10`. The cause is in the code, not in ten data
points: `pursuer.rs::step` rolled `p_lock` once per **control step**, so the
probability of acquiring within a second was `1 − (1 − p_lock)^(1/dt)` and the
pursuer's lethality was a function of `sim.dt`. A reviewer reads that as a
modelling error rather than a calibration, and they are right to.

*The fix, and why it changes no published number.* `p_lock` is now defined as the
acquisition probability per **0.1 s attempt window** — the value every number in
the record was measured at — and converted to a per-step probability by
`1 − (1 − p_lock)^(dt / 0.1)`. At `dt = 0.1` the exponent is one and the function
returns `p_lock` bit-for-bit, by an explicit branch rather than by trusting
`powf(x, 1.0) == x`. One RNG draw is consumed per attempt either way, so the
stream is unchanged as well as the comparison. **The only runs in the whole record
with both a pursuer and `dt ≠ 0.1` are the five `dt = 0.05` pseudo-reality pursuit
sweeps**, which is why the re-run is those five and nothing else.

*What is re-run.* Comparisons 3, 4 and 5 — the pursuit comparisons — on models
02, 03, 04, 05 and 10 only. Comparisons 1 and 2 are aggregation and contain no
pursuer, so they are untouched. Under 1 core-hour.

*How it is reported.* Three statements, in this order and never collapsed into
one: (a) the registered rule fired FRAGILE on comparison 5 under the registered
family; (b) the cause was diagnosed as a per-step Bernoulli standing in for a
per-second rate; (c) under the corrected pursuit the same five models give
whatever they give. **Whether comparison 5 becomes robust or not, that sequence is
the result** — a fixed model that still flips is as publishable as one that does
not, and reporting only (c) would be presenting a re-run as if it were the
pre-registered test.

*Scope, stated because the fix is narrower than the finding.* The audit of every
per-step quantity in `pursuer.rs` is in the run log. One further `dt` dependence
is found and **not** fixed, because fixing it would not be bit-neutral: the
handling-time debt is paid in whole control steps, so `h = 1.93 s` is really
2.000 s of idle at `dt = 0.1` and 1.950 s at `dt = 0.05`, a **2.5%** difference in
the same direction as the `p_lock` error. It is a quantisation of a correctly
per-second quantity, it is two orders smaller than the effect it sits beside, and
it is disclosed rather than corrected.
