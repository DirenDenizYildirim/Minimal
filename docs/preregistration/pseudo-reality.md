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

*(none yet)*
