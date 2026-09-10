# Pre-registration — the tuning control at a second correlation length (freeze lift 1, experiment 3)

Filled from `template.md` and committed **before** the sweep runs. The commit hash
of this file is what makes the rule below pre-registered; `docs/findings.md` §24
will cite it.

## Question

A2 and A3 decompose the gap between the enumerated row and a terrain-tuned one:
the **matched-controller cost** is 10–20%, and the **terrain-tuning term** has an
interval that **includes zero** — most of what looked like terrain robustness was
objective-tuning. Both were measured at a single correlation length, λ = 0.10 m,
which is also the λ every terrain sweep in the record has used since §4 located
the peak there. Does the decomposition depend on that choice?

## Task and threshold

* Behaviour: aggregation.
* Primary metric: **hold ratio** — dispersion at θ_m divided by the *same run's*
  dispersion on flat ground, paired by run index, median of the per-run ratios
  with a 95% percentile-bootstrap CI. §12.1 D1's single definition.
* Threshold `T`, direction: lower is better. The rule below turns on whether an
  interval contains zero, not on a bar.
* Secondary metrics, reported but not thresholded: the **paired terrain-tuning
  term** — the per-run difference `D(S2-flat) − D(S2-rough)` at θ_m = 0.9, with its
  bootstrap interval — and the **level decomposition** (objective-tuning share and
  terrain-tuning share of the anchor-to-rough gap); absolute dispersions; the
  flat-versus-rough crossing if one occurs.
* Cluster link distance: 3.0 body radii.

**Why the decomposition is not paired-ratio'd, and this is deliberate.** A
decomposition needs two shares that add to the whole, which requires additive
*level* estimates: `median(gauci) − median(flat)` plus
`median(flat) − median(rough)` is exactly `median(gauci) − median(rough)`, and no
per-run ratio has that property. Per-run shares are also ill-conditioned here —
`scripts/recompute_paired_and_survival.py` records the per-run gap as negative in
11 of 100 runs at 0.74 m and 31 of 100 at 1.5 m, so a median of per-run shares is
an artefact of sign changes in the denominator. The **paired significance test on
the terrain term is reported alongside**, which is the quantity the rule turns on.

## Capability rows

The three rows of `terrain_tuning_control.toml`, constants copied **verbatim**.
Nothing is re-searched: re-searching at each λ would answer "does a controller
tuned at this λ do better here", which is a different and much more expensive
question, and would destroy the pairing that makes this a control.

| Row | S | M | A | K | Provenance | Free constants | Trained at |
|---|---|---|---|---|---|---|---|
| S2-gauci | 2 | 0 | no | 0 | enumerated | 4 | Gauci's own objective, not this one |
| S2-flat † | 2 | 0 | no | 0 | optimiser_found | 4 | θ_m = 0.0, λ = 0.10 m |
| S2-rough † | 2 | 0 | no | 0 | optimiser_found | 4 | θ_m = 0.9, λ = 0.10 m |

S2-flat and S2-rough differ **only** in the θ_m of their training condition —
same optimiser, budget, training seed base (900000), evaluation seeds, n, τ, start
radius and metric. That is what makes the difference between them the terrain half
of the tuning, and it is the whole design.

Both searched rows are **upper bounds** and carry †.

**A limitation this design cannot remove, stated now.** Both searched rows were
trained at λ = 0.10 m. Evaluating them at λ = 0.05 m and 0.20 m therefore measures
*transfer of a λ = 0.10-tuned controller*, not *the decomposition a controller
tuned at that λ would show*. A terrain-tuning term that shrinks at the new λ is
consistent with two different readings — the term is genuinely small everywhere,
or the term is real but does not transfer — and this experiment cannot separate
them. The findings section must say so and the paper must not read the first
without the second.

## Environment grid

| Dial | Values | Notes |
|---|---|---|
| `terrain.correlation_length` λ | **0.05 m, 0.20 m** | 0.10 m is the existing record and is **not** re-run |
| `terrain.friction_amplitude` θ_m | 0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9 | identical to `terrain_tuning_control.toml` |

Fixed: `swarm.n = 20`, start radius **R = 0.74 m** from `swarm.init.coverage = 0.05`,
`sim.duration = 600.0`, slope 0, no occlusion, no actuation noise, `dt = 0.1` —
every one of them identical to `terrain_tuning_control.toml`, so λ is the only
dial that moves between this sweep and the existing one.

**Why 0.05 and 0.20 m.** They bracket 0.10 m by a factor of two either way and
both sit inside the range §15's λ sweep covered (2–20 cm) with reach ≥ 0.8, so
neither is a cell where the swarm fails to aggregate for reasons unrelated to
tuning. 0.20 m is also λ/R₀ = 1.38 for Gauci, past the peak, and 0.05 m is
λ/R₀ = 0.35, before it — so the pair straddles the peak rather than sampling one
side of it twice.

## Design

* Runs per cell: **100**. Config: `configs/sweeps/terrain_tuning_control_lambda.toml`.
* Seed: `20260904` — **the same base seed as `terrain_tuning_control.toml`**, so
  run *i* is the same placement at every λ and the new cells pair by run index
  against the existing ones. This is what makes "the same experiment at a different
  λ" true rather than approximate.
* Statistics: paired hold ratios and the paired terrain term with bootstrap CIs,
  through `swarm_harness.stats`; the decomposition through
  `scripts/recompute_paired_and_survival.py`, extended additively to the new file.
  Every number is added as an `item(...)` to `scripts/verify_numbers.py`.
* Search budget: **none — nothing is searched here.**

## Predictions

* **H1.** The terrain-tuning interval includes zero at both new λ, as it does at
  λ = 0.10 m (+0.0818 [−0.0008, +0.1331]) and at R = 1.5 m (−0.0124 [−0.1116,
  +0.0775]). The reasoning is §13's: most of the gap is objective-tuning, and the
  objective does not change with λ.
* **H2.** The matched-controller cost stays in single or low double digits and the
  three-λ range is narrower than the 10–20% A2 currently states, because 10–20% was
  read off one λ and two radii.
* **H3.** The flat-versus-rough crossing seen at θ_m = 0.6, λ = 0.10 m
  (+0.0421 [+0.0107, +0.0659]) does **not** reappear at either new λ. It was small,
  it did not survive the move to R = 1.5 m (−0.0008 [−0.0134, +0.0433]), and a
  crossing that appears at one λ and one radius is most likely a coincidence of
  that cell.

## Pre-registered decision rule

**Per λ, reported separately. The three correlation lengths are not pooled.**

* **A3 holds at that λ** if the **paired terrain-tuning interval includes zero**
  there.
* **A3 fails at that λ** if the interval **excludes** zero. Direction matters and
  is reported either way: an interval excluding zero *above* means terrain-tuning
  buys something real at that λ, which would narrow A3 rather than overturn it; an
  interval excluding zero *below* means the terrain-trained row is worse than the
  flat-trained one under terrain, which would be a stronger result than A3 and must
  not be reported as a mere failure.
* **The matched-controller cost is reported as a range across the three λ**
  (0.05, 0.10, 0.20 m), replacing the single-λ figure A2 currently quotes. If the
  range is wider than the currently stated 10–20%, A2's wording changes to the
  measured range; if narrower, it is tightened. Either way the number in the paper
  becomes a range over λ and says so.
* The crossing is reported if present at any λ, with its interval, and is **not**
  claimed as a result unless it is disjoint from zero at more than one λ.

## Budget

`--dry-run` before running, reported at the **× 2.1** correction the Phase 0
review set. 3 rows × 8 θ_m × 2 λ × 100 runs = 4 800 trials at n = 20, τ = 600 s.
Stop and report rather than reduce runs per cell if the revised **60 core-hour**
plan ceiling is threatened.

## Deviations

Anything that changed after registration, and why. Append; do not edit above.

*(none yet)*
