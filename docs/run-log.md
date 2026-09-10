# Run log

Every `swarm sweep`, `swarm search`, figure script and verification command that
produced a file in `results/` or `figures/`, with the git hash it ran at, when it
ran, the wall time and the output path.

`results/` and `figures/` are generated and not committed (README). This file is
what makes them recoverable: it is the answer to "send me the source of Figure 9".

**How to read a row.** The command is literal — copy it and it runs. Sweeps and
searches go through `scripts/regenerate_record.sh` and figures through
`scripts/regenerate_figures.sh`, which are the same commands with the logging
attached; `scripts/regenerate_record.sh <job>` re-runs one group and
`scripts/regenerate_figures.sh <script>` one figure. Every run is seeded from
`(sim.seed, run_index)`, so a re-run reproduces the file bit-for-bit;
`scripts/verify_determinism.py` is the check that it does.

Wall time is on a 4-core machine unless a row says otherwise, and "size" is the
output file on disk. Nine rows say "wall reconstructed": their log lines were
lost to a `git checkout` of this file during Phase 0 and the wall times were
recovered from the output files' modification times, which bound each sweep
between the previous file's write and its own. The commands and outputs in those
rows are exact — they come from `scripts/regenerate_record.sh`'s manifest, which
is what produced them.

## Environment

| item | value |
|---|---|
| host | 4 cores, 15 GB RAM, Linux 6.18 |
| rustc / cargo | see `rust-toolchain.toml` (pinned) |
| Python | 3.11, `uv venv .venv && uv pip install --python .venv/bin/python -e 'harness[stats]'` |
| binary | `cargo build --release` → `target/release/swarm` |
| tests | 110 Rust (96 `swarm-core`, 14 `swarm-cli`, 1 ignored calibration probe) + 32 harness |

---

## Freeze lift 1 — Phase 0: regenerating the frozen record

The evidence base was frozen at `ce427a8`. `results/` and `figures/` are not
committed, so Phase 0 regenerates every file `scripts/verify_numbers.py` and the
§10 figure inventory refer to, and checks them against `docs/paper-source.md` §13.

### Workload

Estimated from `--dry-run` before anything ran, at a measured 725 000
robot-timesteps per core-second:

| group | trials | robot-timesteps | est. core-hours |
|---|---|---|---|
| 40 sweep configs | 146 910 | 25.5 × 10⁹ | 9.8 |
| 9 searches | 122 400 | ~30 × 10⁹ | ~11 |
| **estimated total** | **269 310** | **~55 × 10⁹** | **~21** |

Measured: **11.12 h wall** over 51 sweep and search invocations — 4.28 h of
sweeps and 6.83 h of searches, of which `search_s2_class_rough_tau` alone is
2.9 h (its two τ = 3600 s conditions cost 2.67× the others, as its own config
header predicts). Figures add 40 s. Four cores were available throughout, so
44.5 core-hours is an upper bound on what the driver consumed; the true figure
is lower because several hours overlapped with the diagnostic runs recorded
under "Findings" below. The estimate was low mainly because the throughput model
was linear in `n` where collision resolution and the line-of-sight sensor are
both quadratic, and because it read `τ` from the dry run but not `dt`.

**On the rule 9 budget gate.** Several regeneration sweeps exceed 2 × 10⁶
robot-timesteps × 100 on their own — `phase0_seeds` is 1.0 × 10⁹,
`terrain_class_eval_tau` 2.1 × 10⁹. They were run anyway: their cell counts and
runs/cell are fixed by the frozen configs, cutting runs/cell is forbidden by the
same rule, and the plan as a whole is inside the ceiling. This is recorded rather
than waved through.

**Revised gate, in force from Phase 2** (set on review of this phase): the
whole-plan ceiling is **60 core-hours**, and because the dry-run throughput model
proved about 2× optimistic here, every Phase 2–5 estimate is reported as the
dry-run figure **× 2.1**.

**Revised again on review of Phase 2.** The robot-timestep line had no bite on
this simulator — one 100-run cell at n = 20, τ = 600 s is already 12 × 10⁶, so any
experiment with ≥ 17 such cells crossed it, and Phase 2 crossed it at 4.6% of the
plan ceiling. It is replaced by a **per-experiment blocking threshold of 10
corrected core-hours**; the 60 core-hour plan ceiling stands. Both are reported
before each experiment runs, at the ×2.1 correction.

### Findings

Three groups of §13 rows do not reproduce. Each is diagnosed to a commit, and
**§13 has not been edited**. `scripts/check_section13.py` is the check.

| # | §13 rows | what | cause |
|---|---|---|---|
| F1 | 13, 14 | dispersion 1.401 at every link distance; single-cluster share 0.43 → 0.98 | produced at `axle_length = 0.053`, the value `47a5dd5` corrected to 0.051 |
| F2 | 23, 24 | the θ_m = 1.0 peak-degradation spreads, 5% and 560% | produced before `e83675e` added `traction_floor = 0.05`; at θ_m = 1.0 the multiplier reaches 0.0002 and the floor binds |
| F3 | 56, 57, 58 | the four single-condition searches' objectives and warm-start L2 | the optimiser seed is not recorded by §7, §9 or §10; seeds 1–4 all give something else |

**F1.** `validation.md` §3's whole table comes back cell for cell at
`axle_length = 0.053` — 0.73 / 0.43 / 1.401, 0.87 / 0.61 / 1.401, and so on — and
at 0.051 it is 0.533 / 0.475 / 1.3875. Ruled out first: no run count in 5…100 of
that seed stream medians to 1.401, and a binary rebuilt at the cited commit
`2441bfc` returns 1.3875 like HEAD. So the section was not regenerated when
`2441bfc` regenerated everything else "at the corrected constants", and §13 rows
13–14 inherit it — the one place the axle correction did not propagate, which
§13 row 2 records as having been made. The substance is unaffected: dispersion is
still exactly invariant to the link distance, spread 0 across 2.2 R…6.0 R, which
is what ADR 0003 rests on.

*Corrected values, regenerated at `axle_length = 0.051` (30 runs/cell, as the
config states), for Phase 6 to replace rows 13 and 14 with:*

| link distance | one cluster at τ (Wilson) | share of time single (median) | final dispersion (median) |
|---|---|---|---|
| 2.2 R | 0.53 [0.36, 0.70] | 0.475 [0.459, 0.492] | 1.3875 [1.3559, 1.4625] |
| 2.5 R | 0.77 [0.59, 0.88] | 0.656 [0.623, 0.672] | 1.3875 |
| 3.0 R | 0.77 [0.59, 0.88] | 0.803 [0.787, 0.828] | 1.3875 |
| 3.5 R | 0.87 [0.70, 0.95] | 0.885 [0.869, 0.918] | 1.3875 |
| 4.0 R | 0.93 [0.79, 0.98] | 0.943 [0.934, 0.951] | 1.3875 |
| 5.0 R | 1.00 [0.89, 1.00] | 0.967 [0.967, 0.967] | 1.3875 |
| 6.0 R | 1.00 [0.89, 1.00] | 0.967 [0.967, 0.984] | 1.3875 |

Row 13 becomes **1.3875 at every value**, spread exactly 0; row 14 becomes
**0.475 → 0.967**. The invariance the row exists to state is if anything cleaner
than before.

**F2.** The same sweep at θ_m = 0.7 reproduces §4's table exactly — 1.17, 2.69,
1.40, 1.34, 1.58, each at the published λ — because there the traction multiplier
bottoms out at 0.300, above both the old `.max(0.0)` and the new floor. At
θ_m = 1.0 it bottoms out at 0.0002. Re-running the `base` row at HEAD with
`terrain.traction_floor = 0.0` gives 2.951 / 2.967 / 2.677 at λ = 0.05 / 0.10 /
0.20 against §13's published peak of 2.97. The R₀-versus-axle conclusion is
unaffected in direction and is stronger at HEAD: 44% against 648%, rather than
5% against 560%.

*Corrected values, regenerated with the floor in place, for Phase 6:*

| row | published (θ_m = 1.0) | corrected (θ_m = 1.0) |
|---|---|---|
| 23 — axle 4× at fixed R₀ | 2.83 / 2.97 / 2.93, spread **5%** | 2.21 / 2.74 / 3.18, spread **44%** |
| 24 — R₀ 4× at fixed axle | 1.59 / 2.97 / 10.46, spread **560%** | 1.65 / 2.74 / 12.37, spread **648%** |

**Nothing in scope moves at all**, which is a slightly stronger statement than
"the in-scope difference is rounding". Below θ_m = 1.0 the traction multiplier
cannot reach the floor — at the paper's ceiling of 0.9 its minimum is
1 − 0.9 × 0.9998 = 0.100, twice the floor — so no cell the paper quotes is
touched, and this sweep's highest in-scope amplitude, θ_m = 0.7, reproduces cell
for cell. The 2.967-against-2.97 check above is at θ_m = 1.0 under the *old*
clamp: it shows the published number was computed correctly for the model of its
day, not that the in-scope effect is small. Rows 23 and 24 are the only two §13
rows quoted from the stall band, and correction #10 already cut that band from
the figures.

**F3.** Ruled out: the simulator (`terrain_h3_capability`, the evaluation sweep
from the same commit, reproduces exactly), the search code (a binary built at
`9af4707` returns byte-identically the same constants as HEAD over the full
600-evaluation budget), the configs (never edited since), and the CLI defaults
(budget 600, 12 runs, seed 1, training seed 900 000 at both commits). What is
left is `--seed`. Seeds 1–4 give 1.2737 / 1.2821 / 1.2935 / 1.2916 — every one
*better* than the published 1.3009 — and 1.3009 appears in no seed's incumbent
history, so the published run is not a shorter prefix of one of them either.

The scope is exact and is the argument for this file existing: **all five class
searches reproduce bit-for-bit**, constants and objectives to every digit §13
quotes, including the 1.9302 that only §12.1 mentions in passing. §19–§21 state
their optimiser seeds; §7, §9 and §10 do not.

Nothing downstream is lost to F3 — every evaluation sweep hard-codes the
published constants in its own config, and those sweeps all reproduce. What is
not currently true is "run this command and you get this controller".

**And the published rows are ordinary draws, not lucky ones.**
`configs/diagnostics/f3_seed1_rerun_sanity.toml` scores each published row
against the controller the same protocol returns at optimiser seed 1, at that
row's own training cell, 100 runs on the held-out evaluation seed, paired by run
index:

| training cell | published | re-run, seed 1 | paired ratio re-run / published |
|---|---|---|---|
| S2-rough, θ_m = 0.9, λ = 0.10 m | 1.3834 [1.3505, 1.4409] | 1.3646 [1.3390, 1.4014] | 0.9832 [0.9380, 1.0139] |
| S2-flat, θ_m = 0.0, λ = 0.10 m | 1.2031 [1.1991, 1.2103] | 1.2063 [1.2014, 1.2138] | 1.0019 [0.9910, 1.0091] |

Both paired intervals include 1 and both pairs of marginal intervals overlap. So
the re-runs' better *training* objectives (1.2737 against 1.3009) buy nothing on
held-out seeds — which is C5/S16's winner's curse showing up again, from the
other side: a search's returned objective ranks its own draw and not the
controller. This is a sanity check on the rows of record, not a claim.

### Verification

* `scripts/check_section13.py` — of the 98 §13 rows `verify_numbers.py` covers:
  **76 match**, 2 match with their ids crossed between the two documents (71/72),
  11 recompute a statistic §13 retired in the Phase A revision and are verified
  instead by `scripts/recompute_paired_and_survival.py`, 1 is the difference
  §12.1 already records, 1 is a re-seeded resample whose underlying data
  reproduces (row 114, corroborated by row 117), and **7 are F1–F3**.
* `scripts/recompute_paired_and_survival.py` — every §13 value that came from it
  reproduces exactly: survival 0.4324 / 0.5851 / 0.5188 / 0.6079, the matched
  pair at 0.47 R 0.3636 / 0.4875 / 0.6238, the decomposition 96.9% / 3.1% with a
  terrain term of +0.0818 [−0.0008, +0.1331] that includes zero, and the paired
  hold ratios 2.149 / 1.200 / 1.099.
* `scripts/verify_determinism.py` — **7 of 7 cells IDENTICAL**, 35 runs, every
  compared output field bit-for-bit equal to the logged value.

### Figures

All **26** figures in the §10 inventory now come from a committed script; none
is drawn by hand. Eleven of them had no runnable provenance at all
(verification-report D9 recorded the `swarm-figure` subcommand and none of its
arguments, and the one attempted reconstruction differed from the committed
image in 44% of pixels). The new scripts are `figures_gauci_scaling.py`,
`figures_occlusion_shakedown.py`, `figures_terrain_idea_a.py`,
`figures_terrain_h2.py`, `figures_terrain_mechanism.py`,
`figures_terrain_h3_capability.py` and `figures_terrain_retune_cost.py`. They
reproduce the figure §10 *describes*, not the lost image byte-for-byte, and
where the section's own text names a result the original panel could not show,
the script draws it and the caption says so.

**`docs/paper-source.md` §10's "script / command" column still says
`swarm-figure` for those eleven rows and is now stale.** It is left alone here
because Phase 0 does not authorise editing the source document; the correction
belongs in Phase 6.

---

## Freeze lift 1 — Phase 2: a *searched* S = 3 pursuer row

Pre-registered at `docs/preregistration/searched-s3-pursuer.md`, commit
**`577f15a`**, before any code was written or any search ran.

### What existed, and what had to be added

The pre-registration's "check first" came back: `swarm search` already searched a
`kind = "table"` controller at `sensor.encoding = "ternary"` over six constants,
and a `[pursuer]` block was already live during a search (a 5-run probe at
r_p = 0.35 m, κ = 2.5 gave 0–8 captures per run). Only the objective was missing.

`--objective` was added at **`e18a356`**, defaulting to `dispersion`. Rule 2's
bit-neutrality check: `scripts/verify_determinism.py` byte-identical before and
after, and a budget-40 search agreeing with the pre-change binary on every field
it already had, `best_constants` and the whole `history` included. Nine new tests;
119 Rust tests against 110.

The same commit implements finding F3's requirement — search output records the
git hash (with `-dirty` when the tree is not clean) and an FNV-1a hash of the
resolved base config. **All six searches recorded clean hashes**, at `126bde3`,
`e088818` and `1b31dc7`.

### Budget

Dry-run at the ×2.1 correction: six searches 1.67 core-h, three evaluation sweeps
1.08 core-h, **2.75 core-h total** for 137 700 trials and 3 305 Mrts. That crosses
the per-experiment 2 × 10⁶ × 100 line and sits at 4.6% of the 60 core-hour plan
ceiling. Recorded rather than waved through — and worth stating that the literal
gate has little bite on this simulator, since one 100-run cell at n = 20,
τ = 600 s is already 12 Mrts and any experiment with ≥ 17 such cells crosses it.

### The two objectives separated completely

| search | training objective | state-0 arc | state 1 (robot seen) |
|---|---|---|---|
| `survival` s1 | 0.8614 | **1624.8 cm** | (−0.785, −0.785) — ignores it |
| `survival` s2 | 0.8702 | **169.0 cm** | (−0.975, −0.949) — ignores it |
| `survival` s3 | 0.8536 | **160.3 cm** | (−0.737, −0.735) — ignores it |
| `survival_task` s1 | 0.6804 | 8.5 cm | (+0.607, −0.847) — turns toward |
| `survival_task` s2 | 0.6608 | 5.4 cm | (+0.646, −0.838) — turns toward |
| `survival_task` s3 | 0.4581 | 0.5 cm | (+0.155, +0.386) — turns toward |

Every `survival` seed has state 0 and state 1 as near-identical negative pairs:
the robot never stops for a neighbour. That is D-dispersive's construction,
arrived at independently three times **from a B1-ternary starting point**.

### Which rule fired

`scripts/experiment1_decision.py` applies the rule; its thresholds are
transcribed from `577f15a` into named constants so that editing one to fit a
result is a visible act.

**(a) FIRES, on one seed of three, by one cell.** `S3-survival_task-s2` beats
B1-ternary ‡ on mean per-robot survival with disjoint Wilson intervals in
**13 of 25** held-out cells at h = 1.93 s (rule: ≥ 12), loses 1, overlaps 11,
and holds **dispersion among survivors at 1.40 [1.39, 1.42]** against a bar of
3.0 — better than B1's own 1.52. Pooled at h = 1.93 s it is
**0.5125 [0.5081, 0.5169]** against B1's **0.4596 [0.4553, 0.4640]**, disjoint,
and it is wiped out in 16.4% of runs against B1's 24.2%. Seeds 1 and 3 do not
fire (6 of 25, and 6 with 11 losses).

**(b) FIRES on all three `survival` seeds.** State-0 arcs 1624.8 / 169.0 /
160.3 cm against a 50 cm bar, and dispersion among survivors **14 492 / 10 872 /
9 744** against a bar of 10 — two orders of magnitude past D-dispersive's own
370.4. They do not merely abandon aggregation, they fly apart. They also beat B1
on survival in **19 of 25** cells, which is the point: survival alone is easy to
maximise and the row that maximises it is useless.

**Seed spread is 224.8% and 166.4%**, far outside §21's 10% agreement rule, so
§21's branch (b) applies: the baseline is **best-of-three † per cell** and the
scatter is the uncertainty, not a nuisance to average away.

**Winner's curse**, honest re-score at 100 runs per training condition against 2:
`survival` +0.0215 / +0.0339 / +0.0364; `survival_task` **+0.1687** / +0.1007 /
+0.0142. The two-axis objective is markedly noisier to estimate, which is the
same lesson §20 drew at θ_m = 0.9.

### Where the advantage lives, and where it does not

The 13 winning cells are not scattered: they are the **low-κ, mid-range** ones,
where the pursuer is dangerous and confusion does not rescue the swarm. At κ ≥ 2.5
the searched row and B1 converge and B1 edges ahead. At the perfect-perception
corner (r_p = 1.0 m = 1.35 R, κ = 3) the searched row collapses to 0.0335
[0.0265, 0.0423] against B1's 0.0525 — **worse**. The advantage is
regime-specific and the write-up must say so.

At the Pareto cell r_p = 0.2 m, κ = 0 the searched row reaches survival
**0.6795 [0.6587, 0.6996]** against D-dispersive's 0.7040 [0.6836, 0.7236] — an
overlapping interval — while holding the base task at **1.39** against D's
**379.90**. It very nearly matches the task-abandoning row's survival at 273× the
task quality, which is a stronger version of §12's two-axis point than any
hand-designed row could make.

### G4 is split, on review: the capability claim is against B0, not B1

The rule compared against B1-ternary ‡ because B1 was the best S = 3 row in
existence. Now that a searched row exists, the *capability* question — what one
extra sensor state buys — is properly asked against the S = 2 row, **B0-blind**.
Same sweep, same seeds, no new simulation. `searched-s3-pursuer.md` D3 records the
split; the rule itself was neither changed nor re-run.

**G4, the capability claim.** Best-of-three searched S = 3 † beats B0-blind on
mean per-robot survival with disjoint Wilson intervals in **18 of 25** held-out
cells at h = 1.93 s, **0 worse**, 7 overlapping, while holding dispersion among
survivors at **1.41 [1.40, 1.42]** against B0's **1.45 [1.45, 1.47]** — at or
better than the S = 2 row's own task quality. Per seed the counts are 18 / 17 / 14
(0 / 1 / 5 losses), so this does not depend on which seed is picked. Pooled at
h = 1.93 s the three seeds are 0.4802 / 0.5125 / 0.4413 against B0's **0.3655
[0.3613, 0.3697]**, every interval disjoint and above.

The margin over B0 is far wider than the 13-of-25 margin over B1, which is what
should be expected: B1 already beats B0 in 19 of 25. The point of the searched row
is not that it beats B1 by more, but that the *capability* claim now rests on a
row that was **searched** (†) rather than guessed (‡). That is the whole upgrade,
and it is worth saying plainly that B1's 19 of 25 was never weak evidence about
the capability — it was evidence about a guess.

Best-of-three per cell is §21's branch (b) convention and carries a selection
effect: picking the largest of three noisy estimates and then testing it biases
toward "better". The per-seed counts above are given precisely so a reader can see
the conclusion does not depend on the selection.

**G4′, secondary and regime-specific.** A searched S = 3 row beats the
hand-designed B1 ‡ in the low-κ, mid-range regime — 13 of 25 cells, **one seed of
three**, rows converging at κ ≥ 2.5 and B1 edging ahead at the perfect-perception
corner. Its job in the paper is the sentence "the hand-designed rows are close to
what a class search finds", which is itself worth having.

### The survival rows' dispersion is not a near-wipeout artefact

Checked, because a dispersion of 14 492 quoted on a handful of survivors would be
meaningless. It is the opposite:

| row | usable runs (≥ 3 survivors) | survivors: min / p5 / median | runs with ≤ 5 survivors |
|---|---|---|---|
| S3-survival-s1 † | **2500 / 2500** | 10 / 14 / 17 | **0** |
| S3-survival-s2 † | **2500 / 2500** | 9 / 14 / 17 | **0** |
| S3-survival-s3 † | **2500 / 2500** | 9 / 13 / 16 | **0** |
| D-dispersive ‡ | 2476 / 2500 | 3 / 5 / 13 | 200 (8.1%), median dispersion 1068 |
| B1-ternary ‡ | 1479 / 2500 | 3 / 4 / 17 | 173 (11.7%), median dispersion 11 |

The survival rows' dispersions are computed on nearly-full swarms — every run
usable, never fewer than nine survivors. They are not almost-dead swarms with two
robots far apart; they are nearly-intact swarms spread over hundreds of metres.
The caveat belongs instead on **D-dispersive and B1**, whose dispersions do rest
partly on low-survivor runs, and the figure caption says so.

### Seed 3 and the noise floor, for the methods companion

`survival_task` seed 3 returned **0.4581** against seeds 1 and 2 at 0.6804 and
0.6608 — a third of the way down, from the same start, the same budget and the
same training base. Its winner's-curse gap is the *smallest* of the three
(**+0.0142** against +0.1687 and +0.1007), which is the signature of a search that
stalled early rather than one that overfitted: it found a poor point and stopped
improving, so its reported objective was close to honest. Seeds 1 and 2 also
converged on nearly the same controller — state 0 ≈ (−0.4, −0.91), state 1 ≈
(+0.62, −0.84), state 2 ≈ (−0.855, −0.813) — so the distribution is not smooth but
bimodal: two seeds finding the same basin and one stalling.

Flagged for **C4/C5** in the methods companion: `survival_task` has a noise floor
a search can stall in, and this is a measured instance of it in a second objective
and a second dial. §20 found the same shape at θ_m = 0.9 on the dispersion
objective.

---

## Freeze lift 1 — Phase 3: capability flatness at n ∈ {10, 50}

Pre-registered at `docs/preregistration/capability-flatness-n.md`, commit
**`0dd7ae1`**. Nothing was searched: seven existing rows, constants copied
verbatim, evaluated at two swarm sizes. `scripts/experiment2_decision.py` applies
the rule.

**Budget.** 2 800 trials, 504 Mrts, **0.41 corrected core-hours**; the τ
contingency added 1 400 trials and another 0.41. Both inside the 10 core-hour
per-experiment threshold.

### The τ contingency fired, and the whole n = 10 block re-ran

The trigger was fixed before any data existed: any row below 0.8 reach at
n = 10, θ_m = 0.9, τ = 600 s. **S2-gauci came in at 0.71 [0.61, 0.79]** while every
other row sat at 0.99–1.00 — the truncation is specific to the enumerated row,
which is the row the hold ratios are read against. At τ = 3600 s its reach is
**1.00 [0.96, 1.00]**.

### Verdicts, per n, not pooled

| n | τ | best S = 2 row | S4-terrain † | S4-warm † | verdict |
|---|---|---|---|---|---|
| 50 | 600 s | S2-searched **1.0412** [0.9640, 1.1155] | 1.1277 [1.0841, 1.2507] | 1.1175 [1.0673, 1.1814] | **A1 HOLDS** |
| 10 | 600 s *(truncated)* | S2-searched **1.1671** [1.1262, 1.1978] | 1.0549 [1.0348, 1.0927] | 1.0760 [1.0541, 1.1149] | *A1 fails* |
| 10 | **3600 s** *(the rule is evaluated here)* | S2-searched **1.1449** [1.1055, 1.1748] | 1.0490 [1.0275, 1.1124] | 1.1158 [1.0699, 1.1479] | **A1 HOLDS** |

**A1 holds at both n.** But the n = 10 verdict is on a knife-edge and saying so is
part of reporting it. The point estimates barely move between the two trial
lengths — S4-terrain 1.0549 → 1.0490, S2-searched 1.1671 → 1.1449 — and what
flips the verdict is the intervals closing on each other by about 0.02 each. At
τ = 3600 s they overlap by **0.0069 in hold-ratio units, about 0.6% of the
statistic**. This is not "truncation produced the wrong answer"; it is "at n = 10
the two rows are within a hair of each other and the disjointness test lands
whichever side a small change in interval width puts it". The findings section
must say that, and must not report n = 10 as a clean hold.

### The trend in n is the real result here

At λ = 0.10 m, θ_m = 0.9, S4-terrain † against the best S = 2 row:

| n | S4-terrain † | best S = 2 | standing |
|---|---|---|---|
| 10 | 1.0490 [1.0275, 1.1124] | 1.1449 [1.1055, 1.1748] | nominally better, **overlapping by 0.0069** |
| 20 | 1.2116 [1.1577, 1.2513] | 1.0988 [1.0437, 1.1446] | **disjointly worse** (the existing record) |
| 50 | 1.1277 [1.0841, 1.2507] | 1.0412 [0.9640, 1.1155] | overlapping |

The terrain bit's standing improves monotonically as the swarm shrinks: disjointly
worse at n = 20, overlapping at n = 50, nominally ahead at n = 10. A1 survives at
every n under its own rule, but "a terrain bit never helps" is not what this
shows — what it shows is that no S = 4 row was found that is disjointly better,
and that the margin is smallest at the smallest swarm. That is a lead for the
next paper, not a result in this one, and the register entry should carry it as a
limitation rather than as a finding.

The mechanism is at least plausible: at n = 10 the start radius is 0.523 m and a
swarm has fewer neighbours to use as landmarks, so a bit of exogenous information
about the ground may be worth more. Nothing here tests that, and it is recorded
as an observation.

### The three class-flat seeds scatter again

At n = 10, τ = 3600 s: 1.3153 / 1.4239 / 1.3649. At n = 50: 1.2952 / 1.3383 /
1.4509 (s3's interval is the widest at [1.2429, 1.6744]). Best-of-three per cell
is the baseline, per §21's branch (b), and in the event **S2-searched beat all
three class-flat seeds at both n**, so the best S = 2 row is S2-searched rather
than the class baseline in every cell the rule looked at.

## Freeze lift 1 — Phase 4: the tuning control at a second and third λ

Pre-registered at `docs/preregistration/lambda-tuning-control.md`, commit
**`d6c40c8`**; the config was committed at **`9cc4aee`** before the sweep started.
Nothing was searched: the three rows of `terrain_tuning_control.toml`, byte-identical
down to the constants, evaluated at λ = 0.05 m and 0.20 m.
`scripts/experiment3_decision.py` applies the rule.

**Budget.** 4 800 trials, 576 Mrts, **0.46 corrected core-hours** estimated; the
sweep took **241 s wall on 4 cores = 0.27 core-hours actual**, so the ×2.1
correction was conservative here by about a factor of 1.7. Inside the 10
core-hour per-experiment threshold either way.

### The pairing the design rests on is exact, and there is a free control

Run *i* is the same placement at every λ: across all three rows and both new λ,
**100 of 100 run indices agree with the λ = 0.10 m file on both the seed and the
initial dispersion, with 0 disagreements**. And because θ_m = 0 has no traction
field for λ to correlate, the θ_m = 0 row of the terrain-term table is the *same
run* at every λ — it comes back as **−0.0596 [−0.0763, −0.0371] at all three**,
to four decimals. That is a control the design got for free, and it says the λ
axis is reaching the terrain generator and nothing else.

### The rule fired against its own prediction: A3 fails at both new λ

| λ | terrain term at θ_m = 0.9, D(S2-flat) − D(S2-rough) | verdict |
|---|---|---|
| 0.05 m | **+0.0951 [+0.0456, +0.1366]** | **A3 fails — excludes zero ABOVE** |
| 0.10 m *(existing record)* | +0.0818 [−0.0008, +0.1331] | A3 holds |
| 0.20 m | **+0.0368 [+0.0165, +0.0667]** | **A3 fails — excludes zero ABOVE** |

H1 predicted the interval would include zero at both new λ. It does not, at
either. Both failures are in the direction the pre-registration named as
**narrowing A3 rather than overturning it**: terrain-tuning buys something real,
and the finding must be written that way and not as a null that collapsed.

**Why λ = 0.10 m is the one that holds is not that the effect is smaller there.**
Its point estimate (+0.0818) is more than twice λ = 0.20 m's (+0.0368), which
fails. What separates them is interval width: 0.1339 at λ = 0.10 m against 0.0502
at λ = 0.20 m. **A3 holds at λ = 0.10 m by 0.0008** — the lower bound sits eight
ten-thousandths below zero. Two seed-free checks on how thin that is:

* Re-running the same bootstrap at 200 different resampling seeds (the harness
  fixes it at 0, so the published verdict is reproducible and *stands*), the
  λ = 0.10 m lower bound lands above zero for **7 of 200** seeds and below for
  193. At λ = 0.05 m and 0.20 m it is above zero for **200 of 200**.
* A distribution-free sign test on the 100 paired runs: **68/100** favour
  S2-rough at λ = 0.05 m (0.68 [0.58, 0.76]) and **67/100** at 0.20 m
  (0.67 [0.57, 0.75]) — both disjoint from a coin flip — against **59/100** at
  λ = 0.10 m (0.59 [0.49, 0.68]), which is not.

So the honest reading is not "A3 held at one λ and broke at two". It is that
**λ = 0.10 m is the least favourable of the three cells for detecting this effect,
and it is the only cell the paper had measured.** A null result from a single
correlation length was never strong evidence for a null.

### What survives unchanged is the sentence A3 is actually for

The *level* decomposition barely moves:

| λ | objective-tuning | terrain-tuning | gap |
|---|---|---|---|
| 0.05 m | 95.0 % | 5.0 % | 1.5886 |
| 0.10 m | 96.9 % | 3.1 % | 1.7662 |
| 0.20 m | 94.4 % | 5.6 % | 0.8351 |

A3's sentence — "almost none of the re-tuned controller's advantage is terrain
adaptation" — is **better supported by three λ than it was by one**: the terrain
share is 3–6% everywhere. What fails is the *null test* on the paired term, not
the magnitude claim. Those are two different statements and the register entry
has to carry both: the share is small and stable, and it is not zero.

### The crossing is claimed, and its location moves with λ

The pre-registration claims the θ_m = 0.6 crossing only if it is disjoint from
zero at more than one λ. It is disjoint at **2 of 3** — +0.0659 [+0.0296,
+0.0918] at 0.05 m and +0.0421 [+0.0107, +0.0659] at 0.10 m — so it is claimed.
H3 predicted it would not reappear; it did.

But the binary answer undersells what the three curves show. **The θ_m at which
terrain-tuning starts to pay rises monotonically with λ**: the sign flip sits
between θ_m = 0.2 and 0.45 at λ = 0.05 m, between 0.2 and 0.6 at 0.10 m, and
between 0.45 and 0.9 at 0.20 m. Reported as an observation, with **no mechanism
offered**: the obvious one — "shorter λ is a rougher problem at the same θ_m" —
is contradicted by the anchor's own tax below, which is *lower* at λ = 0.05 m
(2.0719) than at 0.10 m (2.1492) because §15 puts the difficulty peak at 7.46 cm,
between them. The crossing location moves monotonically in λ while the difficulty
does not, so the two are not the same phenomenon and nothing here identifies what
the first one is.

### The matched-controller cost widens rather than narrows

| λ | S2-flat † | S2-rough † |
|---|---|---|
| 0.05 m | +21.4 % | +9.0 % |
| 0.10 m | +20.0 % | +9.9 % |
| 0.20 m | +9.6 % | **+1.2 %** (hold ratio 1.0116 [0.9911, 1.0826] — includes 1) |

Range across the three λ and both tuned rows: **+1.2 % to +21.4 %**, against the
**10–20 %** A2 states from λ = 0.10 m alone. H2 predicted it would narrow; it
widened, and the driver is λ = 0.20 m, where a terrain-tuned controller's cost at
θ_m = 0.9 is not distinguishable from zero. A2's number becomes this range and
must say it is a range over λ.

**One definitional wrinkle that is not a λ effect.** A2's "10–20 %" is computed
from §13's *retired* ratio-of-medians hold ratios (1.195, 1.104). Everything here
uses §12.1 D1's *paired* ratios, which on the very same 100 runs give 1.2004 and
1.0988 → 20.0 % and 9.9 %. The λ = 0.10 m column therefore will not match A2's
digits exactly, and the difference is the change of statistic D1 already settled.
It agrees with §14's paired values to four decimals.

### The anchor's own tax is strongly λ-dependent

S2-gauci's hold ratio at θ_m = 0.9 is 2.0719 / 2.1492 / **1.5186** at λ = 0.05 /
0.10 / 0.20 m. The enumerated row loses about half its terrain penalty by
λ = 0.20 m, which is consistent with §15's λ sweep peaking near 0.075 m and is
the reason the gap being decomposed shrinks from 1.77 to 0.84. The shares are
percentages *of that shrinking gap*, which is why 5.6 % at λ = 0.20 m is a
smaller absolute quantity than 3.1 % at λ = 0.10 m — a point the findings section
must make explicitly, because the percentage table alone reads the other way.

### The limitation the design cannot remove

Both tuned rows were **trained at λ = 0.10 m**. At 0.05 and 0.20 m this measures
the *transfer* of a λ = 0.10-tuned controller, not the decomposition a λ-matched
controller would show. A terrain term that grows at the new λ is consistent with
"the term is real everywhere" and with "the term is partly a mismatch penalty the
λ = 0.10-trained row pays away from its own λ", and this experiment cannot
separate them. Answering that needs a search at each λ, which is a different and
much more expensive experiment. This was stated in the pre-registration before
the numbers existed and is repeated here so the finding cannot be quoted without
it.

### Outputs

`results/terrain_tuning_control_lambda.jsonl` (4 800 records),
`figures/terrain_tuning_control_lambda.png` from
`harness/figures_tuning_control_lambda.py`.
`scripts/recompute_paired_and_survival.py` gained the two new λ columns
additively — with the new results file absent its JSON output is byte-identical
to before the change, which is how that was checked.

## Freeze lift 1 — Phase 5: the pseudo-reality robustness check

Pre-registered at `docs/preregistration/pseudo-reality.md`, commit **`367ee93`**,
with deviations D1–D7 appended there — D3–D7 all **before** anything ran.
Following Ligot & Birattari (2020), eleven models: 00 unperturbed, 01–10 drawn
from the pre-registered sampling seed `20260910` by
`scripts/build_pseudo_reality_configs.py`, which executes the draw so the family
is reproducible from the seed rather than transcribed.
`scripts/experiment4_decision.py` applies the rule; `harness/figures_pseudo_reality.py`
draws it, importing every statistic from that script so the figure cannot disagree
with the rule.

**Budget.** 52 800 trials over 22 sweeps, **3 686 Mrts**, **2.97 corrected
core-hours** — the largest of the four experiments and still well inside the 10
core-hour per-experiment threshold. Running total across the whole freeze lift is
about **49 core-hours** against the 60 core-hour plan ceiling, of which Phase 0's
regeneration is 44.6.

### Verdicts, per comparison, never pooled

| # | comparison | verdict | counts |
|---|---|---|---|
| 1 | terrain tax: S2-gauci vs best-of-three S2-class-flat | **ROBUST** | 10/10 same sign, 10/10 disjoint |
| 2 | capability flatness: S4-terrain † vs S2-searched † | *not established either way* | 9/10 same sign, **4/10 disjoint** (needs 7) |
| 3 | confusion through aggregation (three rows) | **ROBUST** | 10/10 sign for all three; disjoint 10, 10, **7** |
| 4 | matched pair B1 ‡ vs D ‡ (three r_p) | *not established either way* | robust at 0.35 m and 1 m; at **r_p = 0.1 m** 10/10 sign but **3/10 disjoint** |
| 5 | searched S = 3 † vs B0 and vs B1 (six orderings) | **FRAGILE** | five of six fine; **S3 † vs B1 at r_p = 1 m flips in 5 of 10** |

Two of the three predictions were wrong, and the way they were wrong is the
result. H1 said comparisons 1 **and 2** would both be robust: 1 is, 2 is not — its
signs hold but its intervals overlap in six of ten models, which is the branch the
pre-registration named "not established either way" and said must not be written
as robustness. H3 said comparison 4 would be at risk **at r_p = 0.35 m**, where
§8's crossing sits: 0.35 m turns out to be its most robust cell (10/10 disjoint),
and the weak one is r_p = 0.1 m, where the effect is real in sign but only −0.003
to −0.040 in size — too small for 2 000 robots to separate. H2 was right:
comparison 3 is robust in sign, everywhere, for all three rows.

### The fragility is located, and it is not in the abstract's claim

Comparison 5 is fragile because of **one ordering out of six**: best-of-three
searched S = 3 † against **B1-ternary ‡** at **r_p = 1 m**, which is the
perfect-perception corner (1.35 R — the pursuer sees the whole starting swarm from
anywhere in it). The same row against **B0-blind** is ROBUST at r_p = 0.1 and
0.35 m and merely *not established* at 1 m, with **no flips at all**.

That distinction matters because of how the Phase 2 review split G4:

* **G4, the capability claim that goes in the abstract**, is against **B0**. Its
  orderings do not flip in any model.
* **G4′, the regime-specific claim**, is against **B1**. That is the one that
  flips, and only at the perfect-perception corner.

Per the pre-registration, a fragile result **does not retract** the claim — it
bounds it. G4′ holds at the design model, which is where it was measured, and the
register entry gains the qualifier that its ordering at r_p = 1 m does not survive
this neighbourhood.

### The flip separates perfectly on the timestep, and the reason is in the code

| | models | flip C5 † vs B1 at r_p = 1 m |
|---|---|---|
| dt = 0.05 s | 02, 03, 04, 05, 10 | **5 of 5** |
| dt = 0.10 s | 01, 06, 07, 08, 09 | **0 of 5** |

The pre-registration forbids a regression, a significance test or a claim of
mechanism from the flip table, and none is made: ten models over six parameters
cannot support one. But the table separates exactly, and **one fact about the code
is not an inference from ten models**. `pursuer.rs::step` re-rolls
`p_lock = 1/(1 + κ·n_local)` on **every acquisition attempt**, and an attempt
happens once per *control step* while the pursuer is unlocked. So the probability
of acquiring within a second is `1 − (1 − p_lock)^(1/dt)`: **a per-step Bernoulli
standing in for a per-second rate.** Halving the timestep doubles the pursuer's
acquisition attempts per second. Handling time is not affected — `self.handling -= dt`
is in seconds and is correct.

§2.2's "the result is independent of the timestep" is about **exact-arc
integration of the motion**, and it is true of the motion. It was never a
statement about the pursuit, and this experiment is where the difference shows.
Mean per-robot survival at r_p = 1 m, pooled over κ, by timestep:

| row | dt = 0.10 (6 models) | dt = 0.05 (5 models) | ratio |
|---|---|---|---|
| B0-blind | 0.0422 | **0.0004** | 0.01× |
| B1-ternary ‡ | 0.0702 | 0.0238 | 0.34× |
| D-dispersive ‡ | 0.3579 | 0.3586 | **1.00×** |
| S3-survival_task-s1 † | 0.0498 | 0.0798 | 1.60× |
| S3-survival_task-s2 † | 0.0492 | 0.0913 | 1.85× |
| S3-survival_task-s3 † | 0.0203 | 0.0185 | 0.91× |

At r_p = 0.1 m every row is within 1–2% of itself across the two timesteps; at
0.35 m the largest move is B0 at 0.81×. **The sensitivity is confined to the
perfect-perception corner and falls hardest on the aggregating rows, while the
dispersive row is untouched.** A reading consistent with that — a stationary
cluster is re-acquired more often when there are twice as many attempts per
second, whereas a dispersed swarm costs the pursuer travel time it cannot recover
by attempting more — is offered as a reading and not as a finding; nothing here
tests it.

**This is a disclosure, not a defect being fixed.** Every published pursuit number
is at dt = 0.10 and stands as measured; changing the pursuer now would invalidate
all of them and violate rule 2. What changes is what may be said: the pursuit
results are **calibrated at dt = 0.10**, the perfect-perception corner is the
regime where that calibration bites, and §2.2's timestep-independence must not be
quoted as covering it. It belongs in Limitations, in §12.3, and in the methods
companion alongside the F3 provenance disclosure.

### Comparison 2's overlap, and comparison 1's caveat

Comparison 2 keeps its sign in 9 of 10 (the rule's threshold) and loses on
disjointness, 4 of 10. The single flip is **model 09** at −0.0554, which is the
model with the largest contact tolerance (1.98e-5) and the second-largest dropout
rate (0.0849) — but **model 01 has the largest dropout of all (0.0906) and does
not flip**, so the table offers no single-parameter story and none is claimed.
The honest summary is that A1's margin at the design point (+0.1133 [+0.0666,
+0.1510]) is not large enough to survive this much implementation noise as a
*disjoint* ordering, which is consistent with experiment 2 finding the same margin
thin in n.

**Comparison 1's robustness has a caveat the rule does not see.** The reach
diagnostic — reported, not thresholded, and added to the script before any Phase 5
number was read — shows S2-gauci reaching a single cluster in only **0.65** of runs
in model 05 and 0.80 in model 03, against 0.94–1.00 for every tuned row in every
model (the reference itself is 0.86 for gauci). Model 05 also carries C1's largest
difference, +1.1811. So part of C1's robustness is the enumerated row failing to
aggregate at all in the noisier models rather than merely being taxed more. That is
a *stronger* version of the same ordering, but it is a different mechanism from the
one A2 states, and the findings section must say so rather than banking the count.

### What this experiment cannot say, in the words that must travel with it

The family perturbs **implementation** choices — actuation noise, sensor dropout,
contact-solver effort, timestep — around the design point. The kinematics, the
traction model, the pursuer's lock-on law and the sensor geometry are identical in
every model. A result robust here is robust to **how carefully the simulator is
integrated and how noisy its sensors are, not to whether the model is right.**
This is not a reality-gap study: no hardware, no ARGoS, no second simulator, and
§12.3 already records that none of those exist. This experiment does not change
that; it answers a narrower question than the objection that prompted it, and the
paper must not let the narrower answer stand in for the wider one.

### Outputs

22 result files `results/pseudo_reality_{aggregation,pursuit}_model_XX.jsonl`
(52 800 records), `figures/pseudo_reality.png` from
`harness/figures_pseudo_reality.py`, and `figures/pursuer_searched_s3_pareto.png`
from `harness/figures_pursuer_searched_s3_pareto.py` — experiment 1's own Pareto
figure with all four kinds of row, which is deviation D2 of this pre-registration.

### Invocations

| phase | commit | command | when (UTC) | output | wall / size |
|---|---|---|---|---|---|
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/gauci_scaling.toml --out results/gauci_scaling.jsonl` | 2026-09-09T11:57Z | `results/gauci_scaling.jsonl` | 190 s / 472K |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/link_distance_sensitivity.toml --out results/link_distance.jsonl` | 2026-09-09T11:58Z | `results/link_distance.jsonl` | 9 s / 172K |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/occlusion_shakedown.toml --out results/occlusion_shakedown.jsonl` | 2026-09-09T12:00Z | `results/occlusion_shakedown.jsonl` | 153 s / 3.4M |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/small_n_noise_probe.toml --out results/small_n_noise_probe.jsonl` | 2026-09-09T12:00Z | `results/small_n_noise_probe.jsonl` | 14 s / 732K |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/small_n_start_radius_probe.toml --out results/small_n_start_radius_probe.jsonl` | 2026-09-09T12:00Z | `results/small_n_start_radius_probe.jsonl` | 2 s / 960K |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/small_n_time_gate.toml --out results/small_n_time_gate.jsonl` | 2026-09-09T12:03Z | `results/small_n_time_gate.jsonl` | 140 s / 1.6M |
| 0.2 validation | `d382f85` | `./target/release/swarm sweep --config configs/sweeps/sensor_fov_gate.toml --out results/sensor_fov_gate.jsonl` | 2026-09-09T12:03Z | `results/sensor_fov_gate.jsonl` | 23 s / 1016K |
| 0.2 validation | `b485750` | `./target/release/swarm sweep --config configs/sweeps/timestep_convergence.toml --out results/timestep_convergence.jsonl` | 2026-09-09T12:06Z | `results/timestep_convergence.jsonl` | 170 s / 2.0M |
| 0.2 validation | `b485750` | `./target/release/swarm sweep --config configs/sweeps/timestep_fov_gate.toml --out results/timestep_fov_gate.jsonl` | 2026-09-09T12:07Z | `results/timestep_fov_gate.jsonl` | 73 s / 1.2M |
| 0.2 terrain | `b485750` | `./target/release/swarm sweep --config configs/sweeps/terrain_idea_a.toml --out results/terrain_idea_a.jsonl` | 2026-09-09T12:09Z | `results/terrain_idea_a.jsonl` | 136 s / 2.5M |
| 0.2 terrain | `b485750` | `./target/release/swarm sweep --config configs/sweeps/terrain_h1_fine.toml --out results/terrain_h1_fine.jsonl` | 2026-09-09T12:14Z | `results/terrain_h1_fine.jsonl` | 277 s / 4.0M |
| 0.2 terrain | `1ef805f` | `./target/release/swarm sweep --config configs/sweeps/terrain_h2_r0_scaling.toml --out results/terrain_h2_r0_scaling.jsonl` | 2026-09-09T12:18Z | `results/terrain_h2_r0_scaling.jsonl` | 258 s / 5.1M |
| 0.2 terrain | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/terrain_h2_powered.toml --out results/terrain_h2_powered.jsonl` | 2026-09-09T12:28Z | `results/terrain_h2_powered.jsonl` | 603 s / 13M |
| 0.2 terrain | `f8b269b` | `filter results/terrain_h2_powered.jsonl -> results/terrain_h2_powered_valid.jsonl where r['terrain.friction_amplitude'] <= 1.0` | 2026-09-09T12:28Z | `results/terrain_h2_powered_valid.jsonl` | 1 s / 11M |
| 0.2 terrain | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/terrain_mechanism.toml --out results/terrain_mechanism.jsonl` | 2026-09-09T12:32Z | `results/terrain_mechanism.jsonl` | 206 s / 4.1M |
| 0.2 terrain | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/terrain_mechanism_regression.toml --out results/terrain_mechanism_regression.jsonl` | 2026-09-09T12:32Z | `results/terrain_mechanism_regression.jsonl` | 21 s / 584K |
| 0.2 terrain | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/terrain_h3_capability.toml --out results/terrain_h3_capability.jsonl` | 2026-09-09T12:35Z | `results/terrain_h3_capability.jsonl` | 193 s / 3.9M |
| 0.2 pursuer | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/pursuer_idea_b.toml --out results/pursuer_idea_b.jsonl` | 2026-09-09T12:36Z | `results/pursuer_idea_b.jsonl` | 57 s / 8.9M |
| 0.2 pursuer | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/pursuer_dispersive.toml --out results/pursuer_dispersive.jsonl` | 2026-09-09T12:37Z | `results/pursuer_dispersive.jsonl` | 53 s / 14M |
| 0.2 pursuer | `f8b269b` | `filter results/pursuer_dispersive.jsonl -> results/pursuer_dispersive_h1.93.jsonl where r['pursuer.handling_time'] == 1.93` | 2026-09-09T12:37Z | `results/pursuer_dispersive_h1.93.jsonl` | 0 s / 6.9M |
| 0.2 pursuer | `f8b269b` | `./target/release/swarm sweep --config configs/sweeps/pursuer_pareto.toml --out results/pursuer_pareto.jsonl` | 2026-09-09T12:37Z | `results/pursuer_pareto.jsonl` | 11 s / 2.8M |
| 0.2 search | `f8b269b` | `./target/release/swarm search --out results/search_s2.json --config configs/search/train_s2_peak.toml --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000` | 2026-09-09T12:43Z | `results/search_s2.json` | 325 s / 4.0K |
| 0.2 search | `f8b269b` | `./target/release/swarm search --out results/search_s2_flat.json --config configs/search/train_s2_flat.toml --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000` | 2026-09-09T12:49Z | `results/search_s2_flat.json` | 354 s / 4.0K |
| 0.2 search | `8ab46dd` | `./target/release/swarm search --out results/search_s4.json --config configs/search/train_s4_peak.toml --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000` | 2026-09-09T12:57Z | `results/search_s4.json` | 477 s / 4.0K |
| 0.2 search | `8ab46dd` | `./target/release/swarm search --out results/search_s4_warm.json --config configs/search/train_s4_peak.toml --budget 600 --runs-per-eval 12 --seed 1 --training-seed 950000 --init [-0.285218,-0.949495,0.935379,-0.226159]` | 2026-09-09T13:06Z | `results/search_s4_warm.json` | 551 s / 4.0K |
| 0.2 tuning | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_retune_cost.toml --out results/terrain_retune_cost.jsonl` | 2026-09-09T13:10Z | `results/terrain_retune_cost.jsonl` | 272 s / 2.7M |
| 0.2 tuning | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_warm_s4.toml --out results/terrain_warm_s4.jsonl` | 2026-09-09T13:11Z | `results/terrain_warm_s4.jsonl` | 68 s / 668K |
| 0.2 tuning | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_tuning_control.toml --out results/terrain_tuning_control.jsonl` | 2026-09-09T13:15Z | `results/terrain_tuning_control.jsonl` | 207 s / 2.0M |
| 0.2 tuning | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_tuning_control_r15.toml --out results/terrain_tuning_control_r15.jsonl` | 2026-09-09T13:18Z | `results/terrain_tuning_control_r15.jsonl` | 199 s / 2.1M |
| 0.2 regime | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_regime_robustness.toml --out results/terrain_regime_robustness.jsonl` | 2026-09-09T13:33Z | `results/terrain_regime_robustness.jsonl` | 901 s / 3.1M |
| 0.2 regime | `52566c2` | `./target/release/swarm sweep --config configs/sweeps/terrain_regime_tau.toml --out results/terrain_regime_tau.jsonl` | 2026-09-09T13:51Z | `results/terrain_regime_tau.jsonl` | 1046 s / 1.6M |
| 0.2 regime | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_regime_tau_flat.toml --out results/terrain_regime_tau_flat.jsonl` | 2026-09-09T14:08Z | `results/terrain_regime_tau_flat.jsonl` | 1068 s / 1.6M |
| 0.2 lambda | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_lambda_sweep.toml --out results/terrain_lambda_sweep.jsonl` | 2026-09-09T14:11Z | `results/terrain_lambda_sweep.jsonl` | 140 s / 2.8M |
| 0.2 lambda | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_lambda_collapse.toml --out results/terrain_lambda_collapse.jsonl` | 2026-09-09T14:11Z | `results/terrain_lambda_collapse.jsonl` | 38 s / 1.1M |
| 0.2 lambda | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_lambda_r0_family.toml --out results/terrain_lambda_r0_family.jsonl` | 2026-09-09T14:15Z | `results/terrain_lambda_r0_family.jsonl` | 233 s / 5.1M |
| 0.2 lambda | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_lambda_r0_family_r074.toml --out results/terrain_lambda_r0_family_r074.jsonl` | 2026-09-09T14:19Z | `results/terrain_lambda_r0_family_r074.jsonl` | 243 s / 5.2M |
| 0.2 lambda | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_lambda_body.toml --out results/terrain_lambda_body.jsonl` | 2026-09-09T14:23Z | `results/terrain_lambda_body.jsonl` | 243 s / 5.0M |
| 0.2 search | `b78ef5b` | `./target/release/swarm search --out results/search_s2_class_flat.json --config configs/search/train_s2_class_flat.toml --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 910000 --class swarm.init.radius=0.74,1.5,3.0 --class swarm.n=20,50` | 2026-09-09T15:15Z | `results/search_s2_class_flat.json` | 3099 s / 8.0K |
| 0.2 search | `b78ef5b` | `./target/release/swarm search --out results/search_s2_class_flat_seed2.json --config configs/search/train_s2_class_flat.toml --budget 1200 --runs-per-eval 12 --seed 2 --training-seed 910000 --class swarm.init.radius=0.74,1.5,3.0 --class swarm.n=20,50` | 2026-09-09T16:08Z | `results/search_s2_class_flat_seed2.json` | 3161 s / 8.0K |
| 0.2 search | `b78ef5b` | `./target/release/swarm search --out results/search_s2_class_flat_seed3.json --config configs/search/train_s2_class_flat.toml --budget 1200 --runs-per-eval 12 --seed 3 --training-seed 910000 --class swarm.init.radius=0.74,1.5,3.0 --class swarm.n=20,50` | 2026-09-09T16:59Z | `results/search_s2_class_flat_seed3.json` | 3044 s / 8.0K |
| 0.2 search | `b78ef5b` | `./target/release/swarm search --out results/search_s2_class_rough.json --config configs/search/train_s2_class_rough.toml --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 920000 --class swarm.init.radius=0.74,1.5,3.0 --class swarm.n=20,50` | 2026-09-09T17:51Z | `results/search_s2_class_rough.json` | 3120 s / 8.0K |
| 0.2 search | `b78ef5b` | `./target/release/swarm search --out results/search_s2_class_rough_tau.json --config configs/search/train_s2_class_rough_tau.toml --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 920000 --class-point swarm.init.radius=0.74,swarm.n=20,sim.duration=600.0 --class-point swarm.init.radius=0.74,swarm.n=50,sim.duration=600.0 --class-point swarm.init.radius=1.5,swarm.n=20,sim.duration=600.0 --class-point swarm.init.radius=1.5,swarm.n=50,sim.duration=600.0 --class-point swarm.init.radius=3.0,swarm.n=20,sim.duration=3600.0 --class-point swarm.init.radius=3.0,swarm.n=50,sim.duration=3600.0` | 2026-09-09T20:45Z | `results/search_s2_class_rough_tau.json` | 10475 s / 8.0K |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_eval.toml --out results/terrain_class_eval.jsonl` | `2026-09-09T21:02Z` | `results/terrain_class_eval.jsonl` | 1004 s / 5.1M (wall reconstructed, see note) |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_eval_tau.toml --out results/terrain_class_eval_tau.jsonl` | `2026-09-09T21:29Z` | `results/terrain_class_eval_tau.jsonl` | 1629 s / 2.7M (wall reconstructed, see note) |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_tau_eval.toml --out results/terrain_class_tau_eval.jsonl` | `2026-09-09T21:42Z` | `results/terrain_class_tau_eval.jsonl` | 765 s / 4.2M (wall reconstructed, see note) |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_tau_eval_tau.toml --out results/terrain_class_tau_eval_tau.jsonl` | `2026-09-09T22:03Z` | `results/terrain_class_tau_eval_tau.jsonl` | 1281 s / 2.1M (wall reconstructed, see note) |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_objective_probe.toml --out results/terrain_class_objective_probe.jsonl` | `2026-09-09T22:07Z` | `results/terrain_class_objective_probe.jsonl` | 260 s / 1.5M (wall reconstructed, see note) |
| 0.2 class | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/terrain_class_objective_probe_far.toml --out results/terrain_class_objective_probe_far.jsonl` | `2026-09-09T22:20Z` | `results/terrain_class_objective_probe_far.jsonl` | 756 s / 740K (wall reconstructed, see note) |
| 0.2 seeds | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/phase0_seeds.toml --out results/phase0_seeds.jsonl` | `2026-09-09T22:33Z` | `results/phase0_seeds.jsonl` | 794 s / 4.1M (wall reconstructed, see note) |
| 0.2 seeds | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/phase0_seeds_tau.toml --out results/phase0_seeds_tau.jsonl` | `2026-09-09T22:54Z` | `results/phase0_seeds_tau.jsonl` | 1262 s / 2.1M (wall reconstructed, see note) |
| 0.2 seeds | `b78ef5b` | `./target/release/swarm sweep --config configs/sweeps/phase0_seeds_objective_probe.toml --out results/phase0_seeds_objective_probe.jsonl` | `2026-09-09T23:01Z` | `results/phase0_seeds_objective_probe.jsonl` | 418 s / 2.2M (wall reconstructed, see note) |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_gauci_scaling.py` | `2026-09-09T23:04Z` | `figures/gauci_scaling.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_occlusion_shakedown.py` | `2026-09-09T23:05Z` | `figures/occlusion_shakedown_curve.png` `figures/occlusion_shakedown_surface.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_idea_a.py` | `2026-09-09T23:05Z` | `figures/terrain_idea_a_curve.png` `figures/terrain_idea_a_surface.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_h2.py` | `2026-09-09T23:05Z` | `figures/terrain_h2_powered.png` `figures/terrain_h2_r0_scaling.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_mechanism.py` | `2026-09-09T23:05Z` | `figures/terrain_mechanism.png`  | 4 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_h3_capability.py` | `2026-09-09T23:05Z` | `figures/terrain_h3_capability.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_retune_cost.py` | `2026-09-09T23:05Z` | `figures/terrain_retune_cost.png` `figures/terrain_warm_s4.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_mechanism_regression.py` | `2026-09-09T23:05Z` | `figures/terrain_mechanism_regression.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_pareto.py` | `2026-09-09T23:05Z` | `figures/pursuer_pareto.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_tuning_control.py` | `2026-09-09T23:05Z` | `figures/terrain_tuning_control.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_decision_rule_regimes.py` | `2026-09-09T23:05Z` | `figures/terrain_decision_rule_regimes.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_regime_robustness.py` | `2026-09-09T23:05Z` | `figures/terrain_regime_robustness.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_lambda_sweep.py` | `2026-09-09T23:05Z` | `figures/terrain_lambda_sweep.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_lambda_collapse.py` | `2026-09-09T23:05Z` | `figures/terrain_lambda_collapse.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_lambda_r0_family.py` | `2026-09-09T23:05Z` | `figures/terrain_lambda_r0_family.png`  | 3 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_lambda_body.py` | `2026-09-09T23:05Z` | `figures/terrain_lambda_body.png`  | 2 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_idea_b.py` | `2026-09-09T23:05Z` | `figures/pursuer_dispersive_kappa.png` `figures/pursuer_dispersive_surface.png` `figures/pursuer_idea_b_surface.png`  | 5 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_class_search.py` | `2026-09-09T23:05Z` | `figures/terrain_class_search.png`  | 4 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_class_tau.py` | `2026-09-09T23:05Z` | `figures/terrain_class_tau.png`  | 1 s |
| 0.4 figures | `f7093a0` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_seed_reproducibility.py` | `2026-09-09T23:05Z` | `figures/phase0_seed_reproducibility.png`  | 2 s |
| 0.3 diagnostic | `377f268` | `./target/release/swarm sweep --config configs/diagnostics/f3_seed1_rerun_sanity.toml --out results/f3_seed1_rerun_sanity.jsonl` | 2026-09-10T12:13Z | `results/f3_seed1_rerun_sanity.jsonl` | 18 s / 336K |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_gauci_scaling.py` | `2026-09-10T12:14Z` | `figures/gauci_scaling.png`  | 4 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_occlusion_shakedown.py` | `2026-09-10T12:14Z` | `figures/occlusion_shakedown_curve.png` `figures/occlusion_shakedown_surface.png`  | 3 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_idea_a.py` | `2026-09-10T12:14Z` | `figures/terrain_idea_a_curve.png` `figures/terrain_idea_a_surface.png`  | 3 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_h2.py` | `2026-09-10T12:14Z` | `figures/terrain_h2_powered.png` `figures/terrain_h2_r0_scaling.png`  | 3 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_mechanism.py` | `2026-09-10T12:14Z` | `figures/terrain_mechanism.png`  | 5 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_h3_capability.py` | `2026-09-10T12:14Z` | `figures/terrain_h3_capability.png`  | 3 s |
| 0.4 figures | `377f268` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_terrain_retune_cost.py` | `2026-09-10T12:14Z` | `figures/terrain_retune_cost.png` `figures/terrain_warm_s4.png`  | 2 s |
| 2 search | `126bde3` | `./target/release/swarm search --out results/search_s3_pursuer_survival_seed1.json --config configs/search/train_s3_pursuer_survival.toml --objective survival --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:44Z | `results/search_s3_pursuer_survival_seed1.json` | 45 s / 8.0K |
| 2 search | `126bde3` | `./target/release/swarm search --out results/search_s3_pursuer_survival_seed2.json --config configs/search/train_s3_pursuer_survival.toml --objective survival --budget 1200 --runs-per-eval 12 --seed 2 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:45Z | `results/search_s3_pursuer_survival_seed2.json` | 48 s / 8.0K |
| 2 search | `126bde3` | `./target/release/swarm search --out results/search_s3_pursuer_survival_seed3.json --config configs/search/train_s3_pursuer_survival.toml --objective survival --budget 1200 --runs-per-eval 12 --seed 3 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:46Z | `results/search_s3_pursuer_survival_seed3.json` | 46 s / 8.0K |
| 2 search | `e088818` | `./target/release/swarm search --out results/search_s3_pursuer_survival_task_seed1.json --config configs/search/train_s3_pursuer_survival_task.toml --objective survival_task --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:47Z | `results/search_s3_pursuer_survival_task_seed1.json` | 72 s / 8.0K |
| 2 search | `1b31dc7` | `./target/release/swarm search --out results/search_s3_pursuer_survival_task_seed2.json --config configs/search/train_s3_pursuer_survival_task.toml --objective survival_task --budget 1200 --runs-per-eval 12 --seed 2 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:48Z | `results/search_s3_pursuer_survival_task_seed2.json` | 74 s / 8.0K |
| 2 search | `1b31dc7` | `./target/release/swarm search --out results/search_s3_pursuer_survival_task_seed3.json --config configs/search/train_s3_pursuer_survival_task.toml --objective survival_task --budget 1200 --runs-per-eval 12 --seed 3 --training-seed 930000 --init [-0.7,-1.0,1.0,-1.0,-1.0,-1.0] --class pursuer.range=0.2,0.35,0.6 --class pursuer.confusion=0.5,2.5` | 2026-09-10T12:49Z | `results/search_s3_pursuer_survival_task_seed3.json` | 45 s / 8.0K |
| 2 eval | `ceda8b6` | `./target/release/swarm sweep --config configs/sweeps/pursuer_searched_s3.toml --out results/pursuer_searched_s3.jsonl` | 2026-09-10T12:53Z | `results/pursuer_searched_s3.jsonl` | 158 s / 42M |
| 2 eval | `ceda8b6` | `./target/release/swarm sweep --config configs/sweeps/pursuer_searched_s3_pareto.toml --out results/pursuer_searched_s3_pareto.jsonl` | 2026-09-10T12:53Z | `results/pursuer_searched_s3_pareto.jsonl` | 19 s / 5.1M |
| 2 eval | `ceda8b6` | `./target/release/swarm sweep --config configs/sweeps/pursuer_searched_s3_rescore.toml --out results/pursuer_searched_s3_rescore.jsonl` | 2026-09-10T12:53Z | `results/pursuer_searched_s3_rescore.jsonl` | 19 s / 5.1M |
| 3 eval | `1582175` | `./target/release/swarm sweep --config configs/sweeps/terrain_capability_n.toml --out results/terrain_capability_n.jsonl` | 2026-09-10T13:42Z | `results/terrain_capability_n.jsonl` | 466 s / 2.4M |
| 3 eval | `493ec46` | `./target/release/swarm sweep --config configs/sweeps/terrain_capability_n_tau.toml --out results/terrain_capability_n_tau.jsonl` | 2026-09-10T13:45Z | `results/terrain_capability_n_tau.jsonl` | 97 s / 1.3M |
| 4 eval | `9cc4aee` | `./target/release/swarm sweep --config configs/sweeps/terrain_tuning_control_lambda.toml --out results/terrain_tuning_control_lambda.jsonl` | 2026-09-10T14:22Z | `results/terrain_tuning_control_lambda.jsonl` | 241 s / 4.2M |
| 4 figures | `b2de8f9` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_tuning_control_lambda.py` | `2026-09-10T14:32Z` | `figures/terrain_tuning_control_lambda.png`  | 3 s |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_00.toml --out results/pseudo_reality_aggregation_model_00.jsonl` | 2026-09-10T16:17Z | `results/pseudo_reality_aggregation_model_00.jsonl` | 49 s / 1.1M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_00.toml --out results/pseudo_reality_pursuit_model_00.jsonl` | 2026-09-10T16:17Z | `results/pseudo_reality_pursuit_model_00.jsonl` | 16 s / 3.4M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_01.toml --out results/pseudo_reality_aggregation_model_01.jsonl` | 2026-09-10T16:18Z | `results/pseudo_reality_aggregation_model_01.jsonl` | 44 s / 1.1M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_01.toml --out results/pseudo_reality_pursuit_model_01.jsonl` | 2026-09-10T16:18Z | `results/pseudo_reality_pursuit_model_01.jsonl` | 13 s / 3.5M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_02.toml --out results/pseudo_reality_aggregation_model_02.jsonl` | 2026-09-10T16:20Z | `results/pseudo_reality_aggregation_model_02.jsonl` | 90 s / 1.1M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_02.toml --out results/pseudo_reality_pursuit_model_02.jsonl` | 2026-09-10T16:20Z | `results/pseudo_reality_pursuit_model_02.jsonl` | 25 s / 3.5M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_03.toml --out results/pseudo_reality_aggregation_model_03.jsonl` | 2026-09-10T16:22Z | `results/pseudo_reality_aggregation_model_03.jsonl` | 93 s / 1.1M |
| 5 eval | `310100b` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_03.toml --out results/pseudo_reality_pursuit_model_03.jsonl` | 2026-09-10T16:22Z | `results/pseudo_reality_pursuit_model_03.jsonl` | 28 s / 3.5M |
| 5 eval | `4d15db6` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_04.toml --out results/pseudo_reality_aggregation_model_04.jsonl` | 2026-09-10T16:24Z | `results/pseudo_reality_aggregation_model_04.jsonl` | 91 s / 1.1M |
| 5 eval | `4d15db6` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_04.toml --out results/pseudo_reality_pursuit_model_04.jsonl` | 2026-09-10T16:24Z | `results/pseudo_reality_pursuit_model_04.jsonl` | 28 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_05.toml --out results/pseudo_reality_aggregation_model_05.jsonl` | 2026-09-10T16:25Z | `results/pseudo_reality_aggregation_model_05.jsonl` | 86 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_05.toml --out results/pseudo_reality_pursuit_model_05.jsonl` | 2026-09-10T16:26Z | `results/pseudo_reality_pursuit_model_05.jsonl` | 24 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_06.toml --out results/pseudo_reality_aggregation_model_06.jsonl` | 2026-09-10T16:27Z | `results/pseudo_reality_aggregation_model_06.jsonl` | 43 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_06.toml --out results/pseudo_reality_pursuit_model_06.jsonl` | 2026-09-10T16:27Z | `results/pseudo_reality_pursuit_model_06.jsonl` | 15 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_07.toml --out results/pseudo_reality_aggregation_model_07.jsonl` | 2026-09-10T16:28Z | `results/pseudo_reality_aggregation_model_07.jsonl` | 44 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_07.toml --out results/pseudo_reality_pursuit_model_07.jsonl` | 2026-09-10T16:28Z | `results/pseudo_reality_pursuit_model_07.jsonl` | 13 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_08.toml --out results/pseudo_reality_aggregation_model_08.jsonl` | 2026-09-10T16:29Z | `results/pseudo_reality_aggregation_model_08.jsonl` | 49 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_08.toml --out results/pseudo_reality_pursuit_model_08.jsonl` | 2026-09-10T16:29Z | `results/pseudo_reality_pursuit_model_08.jsonl` | 16 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_09.toml --out results/pseudo_reality_aggregation_model_09.jsonl` | 2026-09-10T16:30Z | `results/pseudo_reality_aggregation_model_09.jsonl` | 43 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_09.toml --out results/pseudo_reality_pursuit_model_09.jsonl` | 2026-09-10T16:30Z | `results/pseudo_reality_pursuit_model_09.jsonl` | 14 s / 3.5M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/aggregation_model_10.toml --out results/pseudo_reality_aggregation_model_10.jsonl` | 2026-09-10T16:31Z | `results/pseudo_reality_aggregation_model_10.jsonl` | 82 s / 1.1M |
| 5 eval | `5b5bdae` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_10.toml --out results/pseudo_reality_pursuit_model_10.jsonl` | 2026-09-10T16:32Z | `results/pseudo_reality_pursuit_model_10.jsonl` | 24 s / 3.5M |
| 5 figures | `5b5bdae` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_pseudo_reality.py` | `2026-09-10T16:35Z` | `figures/pseudo_reality.png`  | 7 s |
| 5 figures | `5b5bdae` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_pseudo_reality.py` | `2026-09-10T16:36Z` | `figures/pseudo_reality.png`  | 8 s |
| 5 figures | `5b5bdae` | `PYTHONPATH=harness/src .venv/bin/python harness/figures_pursuer_searched_s3_pareto.py` | `2026-09-10T16:37Z` | `figures/pursuer_searched_s3_pareto.png`  | 3 s |
| 5b eval | `79e2fa0` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_02.toml --out results/pseudo_reality_pursuit_fixed_model_02.jsonl` | 2026-09-10T19:07Z | `results/pseudo_reality_pursuit_fixed_model_02.jsonl` | 28 s / 3.5M |
| 5b eval | `79e2fa0` | `./target/release/swarm sweep --config configs/pseudo_reality/pursuit_model_03.toml --out results/pseudo_reality_pursuit_fixed_model_03.jsonl` | 2026-09-10T19:07Z | `results/pseudo_reality_pursuit_fixed_model_03.jsonl` | 27 s / 3.5M |
