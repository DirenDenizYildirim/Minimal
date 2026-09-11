# Verification report — Phase 0

**Scope.** Verify the experimental record before any paper work touches it. No new
experiment was run. The only simulation executed was the §0.4 re-execution of
seven already-logged cells with their own logged base seed and run indices —
re-execution, not a new experiment. Everything else reads logged run files,
committed configs, and the source.

**Reproduce this report with**

```
cargo test --all && cargo clippy --all-targets --all-features && cargo fmt --check
.venv/bin/python -m pytest harness -q
.venv/bin/python scripts/verify_numbers.py            # §0.2
.venv/bin/python scripts/verify_determinism.py        # §0.4
```

**Verdict.** §0.1, §0.3, §0.4, §0.5 and §0.6 pass. §0.2 reproduces 98 of the
130 numbers-table rows from the logged runs; **six discrepancies** are recorded
below, of which four reach a SUPPORTED claim or a sentence in the draft. Two
further findings concern provenance rather than values. **Phase A must resolve
D2, D3, D4, D5 and D6 in `paper-source.md` before any of them is carried into the
draft.**

---

## 0.1 Tests and build — PASS, with one discrepancy

| check | result |
|---|---|
| `cargo test --all` | **96 passed** (core, 1 ignored), **14 passed** (CLI), 0 failed |
| `pytest harness` | **32 passed** |
| `cargo clippy --all-targets --all-features` | **0 warnings, 0 errors** |
| `cargo fmt --check` | clean |
| `controller::tests::published_derived_quantities_reproduce` | **passes** — pins R₀ to 0.1445 m within 5e-5, ω₀ to −0.75 and ω₁ to −5.02 rad/s within 5e-3, and additionally asserts both rotations are clockwise and that state 1 is a pure spin |
| ICR invariance under a scalar field | **two tests, both pass** — `terrain::tests::a_scalar_centre_field_cannot_change_the_turn_radius` (turn radius unchanged to 1e-9 over 500 poses, *and* the traced path stays on the same circle to 1e-9 over 5000 steps) and `terrain::tests::equal_wheel_scaling_would_not_change_curvature` |
| Galilean-shift invariance of line-of-sight readings | **no such test exists** — see D1 |

### D1 — the Galilean-shift claim is not pinned by a test

`paper-source.md` §3.1 states, of the ICR-invariance and Galilean-shift facts,
"**Both facts are pinned by tests**", and the draft repeats "Both are held by
tests". The ICR half is pinned twice over. The Galilean half — that a constant
drift leaves every line-of-sight reading unchanged — appears only as a **doc
comment** on the `drift_removed_extent` test *helper* in `terrain.rs:408`, which
uses the claim to justify removing drift before measuring loop shape. No test
asserts it. It is a correct and elementary statement about a Galilean shift, but
it is argued rather than checked, and the two facts should not be described as
having the same evidential standing.

*Touches:* the Methods paragraph of the draft and §3.1 of the source. No claim ID.

---

## 0.2 Numbers table against logged runs — 98 of 130 recomputed, six discrepancies

Recomputed by `scripts/verify_numbers.py`, which reads only `results/*.jsonl` and
`results/search_*.json` and uses `swarm_harness.stats` for every single-sample
statistic. Full table: run the script. Coverage:

| category | rows | status |
|---|---|---|
| recomputed from logged runs | 98 | 92 match to the last printed digit; 6 discrepancies below |
| model constants and derived quantities (1–7, 15–17, 33, 39–41, 47, 94, 119) | 15 | verified in §0.6 against code and config defaults |
| literature value (8, the 4.24% two-robot failure rate) | 1 | not recomputable here; external |
| §11/§16/§17/§18 regression outputs (59–63, 87–92, 96, 97) | 14 | **covered only indirectly**: their figures regenerate byte-identically (§0.3), and the collapse and peak scripts print 0.9943/0.9999, 0.1351/0.0870, spread 0.0201, 1.39 [0.72, 1.93], 0.948 [0.474, 1.897] and 0.474 verbatim. `figures_mechanism_regression.py` prints no coefficients, so rows 60 and 63 rest on figure identity alone |
| **total** | **130** | |

### D2 — row 9: "93% of pairs reach contact" is not the canonical cell

The canonical n = 2 cell — `gauci_scaling.jsonl`, 100 runs, the sweep the
validation section tabulates — gives **0.88**. The other small-n probes give
92.7% (`small_n_noise_probe`, pooled over a *noise* sweep including non-zero
noise), 91.0% (`small_n_start_radius_probe`, pooled over start radii) and 88.8%
(`small_n_time_gate`). `docs/validation.md`'s own gate row says "**87–93%** of
pairs reach connectivity"; the narrative sentence two paragraphs later hardens
that to "93%", and the numbers table and the draft carry the 93%.

*Touches:* the reproduction narrative in the draft's Methods. **Phase A must
either quote 0.88 (the canonical cell) or quote the 87–93% range with its
sources.**

### D3 — row 10: "~10% still touching at τ" is the wrong column

In the canonical n = 2 cell, `single_cluster` at τ is **0.15**; the value **0.10**
is `fraction_time_single_cluster`, the *share of time* spent as one cluster. The
source and the draft both attach 10% to "still touching at τ".

This also weakens the sentence it supports. The draft says reach and hold differ
"by an order of magnitude" for a pair: 0.88 → 0.15 is **5.9×**, and 0.88 → 0.10
(share of time) is 8.8×. Neither is an order of magnitude.

*Touches:* the draft's Methods; adjacent to **S18** (SUPPORTED, "reach and hold
are different measurements") — the claim survives, the illustrative factor does
not.

### D4 — row 20: 0.89 is the median realised rate, not the mean

At a nominal FN rate of 0.6 with correlation 0.9, the realised rate over the 100
logged runs is **mean 0.8556, median 0.8938**. The published 0.89 is the median.
`paper-source.md` §3 and the draft both call it "the **mean** realised rate".

*Touches:* **S20** (SUPPORTED). The claim — that correlated and i.i.d. dropout
must be compared at matched *realised* rate — is unaffected; the statistic label
is wrong.

### D5 — rows 22–24: the amplitude is not stated, and the count depends on it

All three reproduce **at the amplitudes the §4 ledger states** and only there:

* row 22, at **θ_m = 0.7**: λ/R₀ = 0.69, 0.69, 0.69, 0.69, 0.35 → **4 of 5**, as
  claimed. At θ_m = 1.0 the same rows give 0.69, 1.38, 2.77, 0.35, 0.35 → **2 of 5**.
* row 23, at **θ_m = 1.0**: peaks 2.97 / 2.83 / 2.93, spread **5%** ✓
* row 24, at **θ_m = 1.0**: peaks 2.97 / 1.59 / 10.46, spread **558%** (published 560%)

The numbers table gives no amplitude for any of the three, and the draft repeats
"four of five rows" with no amplitude attached. A reader who applies it at the
top of the swept range gets a different answer.

*Touches:* §6.6 of the draft and correction #13. **Phase A must attach the
amplitude to rows 22–24.**

### D6 — rows 112, 113: the numbers belong to the τ-corrected row, unnamed

`search_s2_class_rough_tau.json` has `best_training_objective` = **1.6009** and a
six-condition honest re-score of **2.6553**. `search_s2_class_rough.json` has
**1.9302** and **2.3456**. The numbers table calls 1.6009 "the returned row's
reported training objective" and 2.6553 "the returned row"'s re-score without
naming which row, and 1.9302 appears nowhere in the source at all.

The pairing is internally consistent — §20 is about the τ-corrected search
throughout, and the worst-condition cell behind rows 114 and 117 is likewise
`S2-class-rough-tau` — so no claim is wrong. But "the returned row" is ambiguous
in a table whose purpose is to be quotable without its section.

*Touches:* **S16** (SUPPORTED). **Phase A must name the row in rows 112–117.**

### D7 — rows 25, 26, 114: re-seeded bootstrap, last printed digit

1.178 [1.158, 1.193] against a published 1.175 [1.154, 1.190]; 0.9795
[0.9726, 0.9857] against 0.980 [0.976, 0.986]; 2.82 log units against 2.79.
`paper-source.md` §12.1 already records the first of these. Same runs, a
re-seeded bootstrap. Not a defect; recorded so it is not rediscovered.

### D8 — the ratio-of-medians statistic is implemented nowhere in the repository

The published hold ratios in §§6, 7, 9 and 13 are a **ratio of medians with an
independent-resample bootstrap**. Reproducing that statistic recovers them to
four digits (2.2075 → 2.208; 1.1951 → 1.195; 1.1040 → 1.104; and 2.208 [1.907,
2.417] against the published 2.21 [1.90, 2.41]). But `swarm_harness.stats`
implements only single-sample helpers, and **every committed figure script uses
the paired ratio instead**. Those numbers therefore cannot be regenerated by
running anything in the repository; they were computed ad hoc when the sections
were written. `scripts/verify_numbers.py` reproduces the statistic explicitly and
says so at the definition.

This is the mechanical reason D1-in-`paper-source` (the two hold-ratio
definitions) survived as long as it did.

---

## 0.3 Figures against logged runs — PASS for the scripted figures, one provenance gap

**All 26 committed PNGs regenerate byte-identically** (md5 over the whole
directory before and after) from the 14 Python figure scripts:
`figures_tuning_control`, `figures_regime_robustness`, `figures_lambda_sweep`,
`figures_lambda_collapse`, `figures_lambda_r0_family`, `figures_lambda_body`,
`figures_class_search`, `figures_class_tau`, `figures_seed_reproducibility`,
`figures_mechanism_regression`, `figures_pareto`, `figures_decision_rule_regimes`,
and `figures_idea_b` in both modes.

### D9 — the CLI-driven figures cannot be regenerated from the recorded provenance

Nine of the inventory's figures are attributed to the `swarm-figure` CLI
(`gauci_scaling`, both `occlusion_shakedown` figures, both `terrain_idea_a`
figures, `terrain_h2_r0_scaling`, `terrain_h2_powered`, `terrain_mechanism`,
`terrain_h3_capability`, `terrain_retune_cost`, `terrain_warm_s4`). §10 records
the **subcommand only** — "`swarm-figure surface --baseline-y`" — and not the
`--x`, `--y`, `--row-key`, `--metric`, `--thresholds`, `--title` or `--out`
arguments, none of which have defaults that make the command runnable. A
reconstructed invocation for `terrain_h2_powered.png` produced an image
differing from the committed one in **44% of pixels**, so the reconstruction is
wrong and cannot be checked against anything.

The **underlying arrays were verified numerically instead**, in §0.2: rows 22–24
(the h2_powered figure), 25–27 (terrain_mechanism), 28–31 (h3_capability),
49–54 (retune_cost), 55 (warm_s4), 11–12 (gauci_scaling), 20–21
(occlusion_shakedown) all reproduce.

*Fix:* record the full invocation for each CLI figure, or port them to scripts.

---

## 0.4 Determinism spot-check — PASS

`scripts/verify_determinism.py` rebuilds a one-cell sweep config for each section
from the committed sweep file (same `base`, same base seed, same row overrides,
`runs_per_cell = 5`) and re-executes it. Run indices 0–4 keep their logged
derived seeds because the sweep derives every run's stream as
`split_seed(sim.seed, run_index)` and uses one base seed across all cells — which
is also what makes the paired statistics legitimate.

| section | file | row | cell | result |
|---|---|---|---|---|
| §9 | `terrain_retune_cost` | S2-searched | θ_m = 0.9 | **IDENTICAL**, 5 runs |
| §13 | `terrain_tuning_control` | S2-flat | θ_m = 0.9 | **IDENTICAL**, 5 runs |
| §14 | `terrain_regime_robustness` | S2-rough | θ_m = 0.9, R = 0.74 m, n = 20 | **IDENTICAL**, 5 runs |
| §15 | `terrain_lambda_sweep` | S2-gauci | λ = 7.46 cm, θ_m = 0.9 | **IDENTICAL**, 5 runs |
| §18 | `terrain_lambda_body` | body-base | λ = 7.46 cm, θ_m = 0.9 | **IDENTICAL**, 5 runs |
| §19 | `terrain_class_eval` | S2-class-flat | θ_m = 0.9, R = 0.74 m, n = 20 | **IDENTICAL**, 5 runs |
| §21 | `phase0_seeds` | S2-class-flat-s2 | θ_m = 0.9, R = 0.74 m, n = 20 | **IDENTICAL**, 5 runs |

35 runs, and every compared output field — the derived seed, both dispersions,
the ratio, cluster count and largest-cluster fraction, both cluster flags, share
of time, time to first cluster, survivors, survival fraction, captures, capture
rate, and both realised occlusion rates — is bit-for-bit equal to the logged
value in all 35.

---

## 0.5 Provenance — PASS

* **28 distinct commit hashes** are cited across §5 and §13. All 28 exist and all
  28 are ancestors of `HEAD` on `claude/project-setup-repo-structure-dmhxq3`.
* Every config and script named in a ledger entry is present at that entry's
  commit. One apparent miss — `configs/sweeps/terrain_h2_powered.toml` absent at
  `c137593` — resolves correctly: §4 cites two commits, `c137593` for the first
  pass and `9b0b994` for the powered sweep, and the file is present at `9b0b994`.
* **Seed bases match the ledger in every case.** `search_s2` and `search_s2_flat`
  both carry `training_seed_base = 900000`, which is the §13 pairing discipline
  ("differing only in the θ_m of its training condition"). The three flat class
  searches all carry 910000 and differ only in `seed` (1, 2, 3), which is exactly
  what §21 claims. `search_s2_class_rough` and `search_s2_class_rough_tau` both
  carry 920000, the §20 pairing. `search_s4_warm` carries 950000, which the §10
  entry states explicitly as deliberately disjoint from the cold search's 900000.

---

## 0.6 Model-to-text consistency — PASS

Read from the code and config defaults, not the docs.

| stated in §2–§3 | in the code | match |
|---|---|---|
| `v_w = v_cmd,w · m_w(x,y) − g_eff·sin α·(ĥ·ŝ)` | `terrain.rs` module doc and `Terrain::apply` | ✓ |
| `m_w = max(1 + θ_m f(x,y), traction_floor)` | `Terrain::traction`, `.max(self.cfg.traction_floor)` | ✓ |
| traction floor 0.05, never binds in range | `TerrainConfig::default` = 0.05; `the_traction_floor_does_not_bind_in_the_swept_range` | ✓ |
| ŝ is **uphill**, minus sign kept (ADR 0002) | `slope_dir` documented as uphill; `gravity_term_is_heading_dependent_and_signed_downhill_positive` | ✓ |
| θ_bit = `θ_m × 0.3476` (the field median) | `terrain_bit`, `friction_amplitude * ScalarField::MEDIAN_ABS` | ✓ |
| field median \|f\| = 0.3476 | `field.rs` `MEDIAN_ABS = 0.3476`, pinned by a test to ±0.02 | ✓ |
| θ_m ceiling 0.9 in sweeps | every terrain sweep config tops out at 0.9; `terrain_h2_powered_valid` at 1.0 for the figure | ✓ |
| `p_lock = 1/(1 + κ·n_local)` | `PursuerConfig::p_lock` | ✓ |
| confusion radius 0.5 m | default `confusion_radius = 0.5` | ✓ |
| capture distance 0.08 m | default `capture_distance = 0.08` | ✓ |
| speed ratio ρ = 1.5 | default `speed_ratio = 1.5` | ✓ |
| handling time 5.0 s default; 0.39 / 1.93 s in the later sweeps | default `handling_time = 5.0`; the dispersive and Pareto configs set 0.39 and 1.93 | ✓ |
| τ = 600 s baseline; 1800 / 3600 s in the τ sweeps | `gauci_baseline.toml` `duration = 600.0`; τ files carry all three | ✓ |
| start radius 0.74 m at n = 20 | derived from `coverage = 0.05`: √(20·0.037²/0.05) = 0.740 m | ✓ |
| validity window: reach ≥ 0.8 at θ_m = 0.9 | `REACH_FLOOR = 0.8` in both `figures_lambda_r0_family.py` and `figures_lambda_body.py` | ✓ |

One stale comment, not a divergence: `Terrain::traction`'s doc says "Clamped at
0" where the code clamps at `traction_floor`. The code and `paper-source.md`
agree with each other.

---

## 0.7 Summary and hand-off to Phase A

**Discrepancies that must be resolved in `paper-source.md` before Phase B:**

| # | what | claim touched | fix |
|---|---|---|---|
| D2 | "93% of pairs reach contact" is not the canonical cell (0.88) | Methods narrative | quote 0.88, or the 87–93% range with sources |
| D3 | "~10% still touching at τ" is the share-of-time column (still touching is 0.15) | adjacent to **S18** | correct the column; the "order of magnitude" becomes 5.9× |
| D4 | 0.89 realised FN rate is the median, not the mean (mean 0.8556) | **S20** | relabel the statistic |
| D5 | rows 22–24 carry no amplitude; the "four of five" count is θ_m = 0.7 only | correction #13, draft §6.6 | attach the amplitude |
| D6 | rows 112–117 name "the returned row" but mean `S2-class-rough-tau` | **S16** | name the row |
| D7 | re-seeded bootstrap in the last digit (rows 25, 26, 114) | none | already noted in §12.1; extend it |

**Provenance findings, no value affected:** D1 (the Galilean claim is argued, not
tested), D8 (the ratio-of-medians statistic exists in no committed script), D9
(the CLI figures' invocations are unrecorded).

**Nothing found invalidates a SUPPORTED claim.** S16, S18 and S20 need wording
repairs, not regrading. The two results a reader is most likely to lean on — the
2×2 tuning control (rows 68–74) and the seed study (rows 118–130) — reproduce to
the last printed digit, as do the whole §14 regime grid, the §19 class-search
grid, and every pursuer κ-response.

---

# Freeze lift 1 — what the re-run found, and the harness corrections

The evidence base was frozen at `ce427a8`. The freeze was lifted once, for four
experiments answering four reviewer objections, and re-frozen at `freeze-2`. This
section records what regenerating the frozen record turned up and what was
corrected in the harness along the way. Every item here is a finding about the
*record or the tooling*, not about the science.

## F1 — rows 13/14 were produced at the wrong axle length

`validation.md` §3's link-distance table and §13 rows 13–14 were computed with
`axle_length = 0.053`. The committed baseline is **0.051** — correction #2, where
5.3 cm was the literature error and 5.1 cm the measured value. **The whole table
returns cell for cell at 0.053**, which settles the cause rather than guessing it.

| | as published | at the committed 0.051 |
|---|---|---|
| dispersion, 2.2 R → 6.0 R | 1.401 at every value | **1.3875 at every value** |
| spread | 0 | **exactly 0** |
| single-cluster share | 0.43 → 0.98 | **0.475 → 0.967** |

**The 0.053 values are kept here with the cause**, §13 carries the corrected ones,
and `validation.md`'s table is left as measured with a note above it — it is what
shows the cause. **Nothing the table is cited for changes**: the invariance of
dispersion to the link distance is exact at both axle lengths.

*Citation audit, run before the correction was applied.* Rows 13/14 are cited by
§7 claim **S18** (qualitative, no digits), §6 claim **C7** (quotes 1.401 and
0.43 → 0.98), §1.5, correction #6 and ADR 0003. The paper-writing notes quote
none of the numbers and reference S18 once by claim id. Both citing passages are
updated.

## F2 — rows 23/24 predate the traction floor

Computed before `e83675e` added `traction_floor = 0.05`. Recomputed with the floor:

| | as published | with the floor |
|---|---|---|
| axle 4× at fixed R₀, θ_m = 1.0 | 5 % (2.97 / 2.83 / 2.93) | **44 %** (2.21 / 2.74 / 3.18) |
| R₀ 4× at fixed axle, θ_m = 1.0 | 560 % (2.97 / 1.59 / 10.46) | **648 %** (1.65 / 2.74 / 12.37) |

**No claim changes**: R₀ still sets the magnitude and the axle still does not, by
an order of magnitude either way. And **there is no in-scope effect at all** — the
cell is θ_m = 1.0, outside the paper's stated range, and at θ_m ≤ 0.9 the traction
multiplier's minimum is 0.100, twice the floor, so the floor is never reached in
any cell the paper quotes. Claim **S9b** quotes all six numbers and is updated.

## F3 — three rows cannot be regenerated, and why

Rows 56, 57 and 58 come from four single-condition searches whose **optimiser
seed is recorded nowhere**: not in the config, not in the output JSON, not in the
run log. Re-running them lands on a different draw.

| controller | published | re-run at HEAD | paired ratio against the published row |
|---|---|---|---|
| warm-start training objective | 1.2595 | 1.2811 | — |
| cold S4 training objective | 1.3012 | 1.3018 | — |
| cold S2 training objective | 1.3009 | 1.2737 | — |
| warm-start L2 from its start | 0.464 | 0.625 | — |
| seed-1 re-runs at their own training cell, 100 runs | — | — | **0.9832 [0.9380, 1.0139]** and **1.0019 [0.9910, 1.0091]** |

**What was ruled out.** The simulator: a binary built at `9af4707` returns
byte-identical constants to HEAD over the full budget. The search code, the
configs, the CLI defaults: all unchanged in the relevant paths. And **all five
class searches reproduce bit-for-bit**, which is the decisive control — the same
code, the same machine, the same command, reproducing exactly when the seed *is*
recorded. The gap is the missing seed and nothing else.

**The published constants are the rows of record and are not replaced.** Both
paired ratios include 1, so the published rows are ordinary draws rather than
lucky ones. **This is a disclosure, not a defect to hide.** §13 carries the note
against the rows, §9 carries limitation L29, and `swarm search` now writes its
optimiser seed, training seed base, budget, git hash and config hash into every
output JSON (`swarm-cli/src/search.rs`), so no later row can enter this state.

## Harness corrections

Found while wiring the later phases. None of them changed a number; all of them
could have.

* **`job_eval_s3` was defined twice** in `scripts/regenerate_record.sh`. Bash
  silently takes the later definition, so it worked and would have kept working
  while the two drifted apart. Fixed at `1582175`.
* **`job_capability_n` was defined but never listed in `ALL`**, so a full re-run
  would have skipped it in silence. Fixed at the same commit, and the driver now
  has a check that every `job_*` is reachable from `ALL` and every `ALL` entry
  exists — run on every change since.
* **`scripts/regenerate_figures.sh` hardcoded `0.4 figures`** in its run-log row,
  which was true of every figure it had drawn until freeze lift 1. The phase is
  now a parameter (`80caaca`); every existing row is unchanged.
* **`scripts/regenerate_figures.sh` aborted at the first script printing no PNG
  path.** `set -euo pipefail` plus a `grep` that exits 1 —
  `figures_mechanism_regression.py` prints only "ok". Fixed with a temp file and a
  fallback that greps the script's own `savefig` calls.
* **`derive()` raised `KeyError` on every sweep coordinate**: sweep coords live
  under `cell`, and the predicate was evaluated against the top level only.
* **§13 rows 71 and 72 were crossed** between `verify_numbers.py` and §13 — the
  script computed the paired form under id 71's label and the ratio of medians
  under 72's, while §13 has them the other way round. **Fixed in the script**,
  which is where the error was: both numbers always reproduced and only the labels
  were swapped.
* **`docs/paper-source.json` was a hand-maintained mirror of §13**, which is how
  the crossing survived a verification pass. It is now generated from the markdown
  by `scripts/sync_paper_source_json.py`, with a `--check` mode that fails if the
  two drift.
* **D9 is closed.** The eleven CLI-driven figures each have a committed script and
  §10 names it. The scripts are **not** byte-for-byte ports and cannot be — there
  is no committed original, and the one reconstruction attempted differed from the
  committed PNG in 44% of pixels. Each script's docstring says so with the date.

## Simulator corrections — both bit-neutral, both disclosures

Two defects of the same class, each found by experiment 4 and each fixed so that
**every published run is bit-identical**.

* **`p_lock` was per control step**, so the pursuer's acquisition rate — and
  therefore its lethality — was a function of `sim.dt`. Now defined per 0.1 s
  attempt window and converted by `1 − (1 − p_lock)^(dt/0.1)`, the identity at
  `dt = 0.1` by an explicit branch. **Twelve pursuit results files regenerated
  byte-identical over 105 800 records.** Five new tests.
* **`noise.wheel_noise` was a fixed-σ Gaussian on wheel speed per step**, so
  accumulated diffusion went as `σ²·dt`. Now `σ_step = σ_ref·√(0.1/dt)` — the
  **reciprocal** of the `σ ∝ √dt` that is correct for a direct increment to a
  state variable, because a velocity noise is multiplied by `dt` before it reaches
  the pose. **Eleven files byte-identical**, including the noise sweep
  (`small_n_noise_probe`, noise at `dt = 0.1`) and the timestep sweep
  (`timestep_convergence`, `dt` from 0.002 to 0.1, noise-free). Four new tests.

**One dt dependence is disclosed and not fixed**: the handling-time debt is paid
in whole control steps, so `h = 1.93 s` is 2.000 s of idle at `dt = 0.1` and
1.950 s at 0.05 — **2.5%**, in the same direction as the `p_lock` error and two
orders smaller. Correcting it would change `dt = 0.1` behaviour and is therefore
not bit-neutral. The full per-step audit of `pursuer.rs`, `world.rs`, `robot.rs`,
`sensor.rs`, `occlusion.rs` and `terrain.rs` is in `docs/run-log.md`, Phases 5b
and 5c.

Rust tests: **119 → 128** (105 core, 23 CLI, 1 ignored); harness tests 32.
