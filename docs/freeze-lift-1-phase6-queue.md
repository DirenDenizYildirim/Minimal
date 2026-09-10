# Freeze lift 1 — the Phase 6 queue

Every edit Phase 6 must make, in one place, written down as it was decided rather
than reconstructed at the end. Wording the reviewer gave verbatim is quoted and
marked **verbatim — do not paraphrase**; everything else is mine and may be
re-worded as long as the substance survives.

This file is a work order, not a source. Nothing here is evidence; each item
points at the findings section, run-log section or results file that is.

---

## 1. §13 rows to replace (Phase 0 findings F1 and F2)

| rows | what changes | cause | recorded in |
|---|---|---|---|
| 13, 14 | row 13 → **1.3875 at every value, spread exactly 0**; row 14 → **0.475 → 0.967** | produced at `axle_length = 0.053`; `validation.md` §3's table returns cell-for-cell at 0.053 | run-log Phase 0 "Findings", `verification-report.md` |
| 23, 24 | row 23 → **2.21 / 2.74 / 3.18, spread 44 %**; row 24 → **1.65 / 2.74 / 12.37, spread 648 %** | produced before `e83675e` added `traction_floor = 0.05` | same |

Keep the 0.053 values in `verification-report.md` with the cause. One line to
`literature-corrections.md`. **No claim changes** in either case: at θ_m ≤ 0.9 the
traction multiplier's minimum is 0.100, twice the floor, so F2 has no in-scope
effect at all — the θ_m = 1.0 cell that S9b quotes is outside the paper's stated
range and the findings must say so.

**Re-grade check already done** (reviewer asked for it before Phase 6): rows 13/14
are cited by §7 claim **S18** (qualitative, no digits), §6 claim **C7** (quotes
1.401 and 0.43 → 0.98), §1.5, correction #6 and ADR 0003. Rows 23/24 are cited by
§7 claim **S9b** (quotes all six numbers, stated at θ_m = 1.0). The paper-writing
notes quote none of the numbers and reference S18 once and S9b twice by claim id.

## 2. §13 provenance note (Phase 0 finding F3)

Add to §13, against rows 56/57/58: **provenance: searched, optimiser seed not
recorded, non-regenerable.** Plus a Limitations line. The published constants stay
— they are the rows of record. *This is a disclosure, not a defect to hide.*
`verification-report.md` carries the table of the four re-run controllers and the
elimination (simulator, search code at `9af4707` byte-identical over the full
budget, configs, CLI defaults; all five class searches reproduce bit-for-bit).

## 3. §7 claims register

### G4 — SUPPORTED †

**Verbatim — do not paraphrase.** Register and abstract:

> One additional sensor state buys survival at fixed task quality: the
> best-of-three searched S = 3 row † beats the S = 2 Gauci row in 18 of 25
> held-out cells at h = 1.93 s (0 worse; per seed 18 / 17 / 14), holding
> dispersion among survivors at 1.41 vs 1.45.

**The per-seed counts travel with the best-of-three number everywhere it appears**
— in the register, in the abstract, in the figure caption, in the findings. They
are the reader's window on the selection bias and there is no version of this
sentence that drops them.

The B1 comparison keeps the framing agreed in the Phase 2 review: **B1's 19/25 was
strong evidence about a guess; the upgrade is provenance, not margin.** That
sentence goes in as written.

### G4′ — SUGGESTED

Best-of-three, regime-specific, with the hedge explicit. Its job in the paper is
the sentence *"the hand-designed rows are close to what a class search finds"*,
which is itself useful. 13/25 cells, thin pass, described honestly — the threshold
was **not** moved after the fact and the findings say so.

### A1 — the grade splits by n

**Verbatim — do not paraphrase.**

> At n = 20, no S = 4 row was found better than the searched S = 2 row at equal
> budget (SUPPORTED †). At n ∈ {10, 50}, the n = 20-searched S = 4 rows are not
> disjointly better than the best S = 2 row (SUGGESTED †: candidates transferred,
> not searched at those n; margin 0.0069 at n = 10).

Two reasons, and **the second must be explicit in the findings**, not left implied:

* **Margin.** Disjointly worse at n = 20, overlapping at 50, overlapping by
  0.0069 at n = 10. n = 10 must not be written up as a clean hold.
* **Candidates.** The S = 4 rows were *searched at n = 20 and transferred*. So at
  n ≠ 20, A1 tests whether n = 20-searched terrain-bit rows help elsewhere — not
  whether any S = 4 row at those n would. **The upper bound at n = 10 is only the
  transferred row.**

Also record that the pre-registered τ contingency fired on Gauci alone at n = 10
(reach 0.71 → 1.00 at τ = 3600 s) **as the rule working**, not as a hitch.

### A9 — new id, OBSERVATION

**Verbatim — do not paraphrase.**

> The terrain bit's standing against S = 2 improves monotonically as n falls
> (1.21 vs 1.10 at 20; 1.13 vs 1.04 at 50; 1.05 vs 1.14 at 10, overlapping).
> Untested mechanism: fewer neighbours to use as landmarks at small n.

Placement: **stated as consistent with P4 of the introduction** — the paper's own
framework says c\* depends on n — **not buried in Limitations.**

### A3 and A2 — from experiment 3

Proposed, pending the reviewer's word (raised at the end of the Phase 4 report and
not yet answered): A3 keeps its grade for the *share* claim (3.1–5.6 % across
three λ, better supported by three than by one) and gains an explicit **"the term
is small but not zero"** qualifier, since the pre-registered null test fails at
λ = 0.05 and 0.20 m in the narrowing direction. A2's 10–20 % becomes the measured
range **+1.2 % to +21.4 %**, said to be a range over λ. Whether the θ_m = 0.6
crossing — now claimed under the rule at 2 of 3 λ — gets its own claim id or stays
a note under A3 is also open.

## 4. §3 P3 — the baseline candidate set

The template stated the c\* baseline as best-of-three over {Gauci, class s1–s3}. In
the A1 cells **S2-searched beat all of them**. Both halves go in §3 P3:

* **For capability comparisons (A1)**, the S = 2 competitor is **the best of every
  S = 2 row evaluated in the cell, including single-condition rows** — the
  conservative choice, since it makes S = 4 harder to beat.
* **For the c\*(θ) baseline as a region (C3)**, the set stays **the class rows**.

Note that at the A1 cells the single-condition row won, and **cross-check that
against C1's cells** (flat ground, three radii, n = 50) so the two do not read as
contradicting: they are different cells and different tasks for the row.

## 5. C3 — seed scatter

Log the n = 10 class-flat scatter (**1.315 / 1.424 / 1.365**) with the others.
The "region, not point" rule holds again.

## 6. Figure captions

* **Pareto figure** (experiment 1, all four kinds of row): note that the
  survival-only rows are **intact swarms spread over hundreds of metres**, and
  that the **≤ 5-survivor caveat applies to D (8.1 %) and B1 (11.7 %)** — not to
  the searched survival rows, which use 2500/2500 usable runs with a minimum of
  9–10 survivors and zero runs at ≤ 5.
* Every caption quoting the best-of-three S = 3 count carries the per-seed counts
  (item 3).
* All new captions carry †/‡ per rule 8.

## 7. `verification-report.md` — harness corrections

A new subsection, "harness corrections", carrying the driver bugs found while
wiring the later phases:

* `job_eval_s3` was **defined twice** in `regenerate_record.sh`; bash silently
  takes the later definition, so it worked and would have kept working while the
  two drifted apart. Fixed at `1582175`.
* `job_capability_n` was **defined but never listed in `ALL`**, so a full re-run
  would have skipped it silently. Fixed at the same commit; the driver now has a
  check that every `job_*` is reachable from `ALL` and every `ALL` entry exists.
* `regenerate_figures.sh` hardcoded `0.4 figures` in its run-log row; the phase is
  now a parameter (`80caaca`).
* The eleven ex-CLI figures: §10's script/command column updated (D9).
* `verify_numbers.py` ids **71/72 crossed** between documents — fix the script to
  match §13, not the other way round.

## 8. Findings sections to write

| § | experiment | pre-registration | run-log section |
|---|---|---|---|
| §22 | 1 — searched S = 3 pursuer row | `577f15a` | Phase 2 |
| §23 | 2 — capability flatness in n | `0dd7ae1` | Phase 3 |
| §24 | 3 — the second and third λ | `d6c40c8` | Phase 4 |
| §25 | 4 — pseudo-reality | `367ee93` | Phase 5 |

Plus `paper-writing-notes-addendum.md`, and every new number added as an
`item(...)` to `scripts/verify_numbers.py` with `check_section13.py` clean.

## 9. Re-freeze

Commit message: `Freeze lift 1: searched S3 pursuer row, n-scaling, second lambda,
pseudo-reality check; re-frozen`. Tag `freeze-2`. Archive `results/` one last time.
