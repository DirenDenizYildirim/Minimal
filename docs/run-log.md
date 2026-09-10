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
