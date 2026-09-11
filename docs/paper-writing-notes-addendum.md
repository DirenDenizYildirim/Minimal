# Paper-writing notes — freeze lift 1 addendum

What changed for the paper between `freeze-1` (`ce427a8`) and `freeze-2`. This is
an addendum: it does not restate the notes it is appended to, and where the two
disagree **this one is later and wins**.

`paper/AI-GENERATED-DRAFT-do-not-circulate.tex` and `paper/AI-DRAFT-notes.md` were
not opened during the freeze lift and are not sources.

## The abstract sentence that changed

**G4 is now SUPPORTED †**, and the sentence to use is fixed:

> One additional sensor state buys survival at fixed task quality: the
> best-of-three searched S = 3 row † beats the S = 2 Gauci row in **18 of 25**
> held-out cells at h = 1.93 s (**0 worse**; per seed **18 / 17 / 14**), holding
> dispersion among survivors at **1.41** vs **1.45**.

**The per-seed counts travel with the best-of-three number everywhere it
appears** — abstract, register, captions, findings. They are the reader's window
on the selection bias. There is no version of this sentence that drops them.

The framing for the B1 comparison, which belongs wherever B1 is mentioned beside
it: **B1's own 19/25 was strong evidence about a guess; the upgrade is provenance,
not margin.**

## Grades that moved

| claim | was | now |
|---|---|---|
| G4 (capability, S = 3) | SUGGESTED | **SUPPORTED †**, against B0 |
| G4′ (regime-specific, vs B1) | — | **SUGGESTED**, new |
| A1 / S2 (capability flatness) | SUPPORTED | **SUPPORTED † at n = 20; SUGGESTED † at n ∈ {10, 50}** |
| A2 (terrain tax) | SUPPORTED, 10–20 % | **SUPPORTED**, a **range over λ: +1.2 % to +21.4 %** |
| A3 (decomposition) | SUPPORTED | **SUPPORTED †**, reworded: small at every λ **and not zero** |
| A8 (the θ_m = 0.6 crossing) | — | **SUGGESTED**, new |
| A9 (terrain bit's trend in n) | — | **OBSERVATION**, new |
| G11 (pseudo-reality) | — | **SUGGESTED**, new |

## Sentences that must not be written

* **"The pursuit is timestep-independent."** §2.2's exact-arc result is about
  integrating the motion. The pursuer's acquisition was a per-step Bernoulli until
  freeze lift 1 and the aggregation dynamics are themselves timestep-sensitive in
  the enumerated row. Methods 4.1 is scoped to motion integration; Methods 4.4
  states `p_lock`'s semantics (probability per 0.1 s attempt window, converted to
  the step by `1 − (1 − p_lock)^(dt/0.1)`); §11 carries the prohibition.
* **"The orderings are robust to the model."** Two of five comparisons came back
  *not established either way*, which is not evidence of robustness. Say which
  comparisons, with both counts.
* **"A reality-gap check."** The pseudo-reality family perturbs how carefully the
  simulator is integrated and how noisy its sensors are, not whether the model is
  right. No hardware, no ARGoS, no second simulator.
* **"Terrain-tuning buys nothing."** A3's null test fails at two of three λ, above
  zero. The share is 3–6 %: small, and not zero.
* **Any hold ratio quoted in both forms.** §13 row 71 is the paired form (§12.1
  D1) and row 72 the retired ratio of medians. They are the same 100 runs. Quote
  one.

## Numbers that changed under a reader's nose

* **A2's 10–20 %** came from the retired ratio-of-medians form. The paired form
  gives 20.0 % and 9.9 % on the same runs. If the paper quotes the range
  (+1.2 % to +21.4 %) it is quoting the paired form and must not also quote the
  old figures as if they were a different measurement.
* **§13 rows 13/14 and 23/24** are corrected (F1, F2). Nothing they are cited for
  changes; the digits do. See `literature-corrections.md` #16 and #17.
* **§13 row 31's interval** is now Wilson, [0.78, 0.91], not the normal
  approximation [0.79, 0.93]. Same point estimate, same runs.

## Where the new material lives

| experiment | pre-registration | findings | §13 rows | figure |
|---|---|---|---|---|
| 1 — searched S = 3 pursuer row | `577f15a` | §22 | 163–168 | `pursuer_searched_s3_pareto.png` |
| 2 — capability flatness in n | `0dd7ae1` | §23 | 169–172 | — |
| 3 — the second and third λ | `d6c40c8` | §24 | 173–179 | `terrain_tuning_control_lambda.png` |
| 4 — pseudo-reality | `367ee93` (+D1–D10) | §25 | 180–189 | `pseudo_reality.png`, `pseudo_reality_corrected_both.png` |

## The two sentences that carry the whole pursuer result

Neither works alone, and quoting either without the other inverts what was found:

> At r_p = 0.2 m, κ = 0 the two-axis searched row reaches **0.6795 [0.6587,
> 0.6996]** against the dispersive row's **0.7040 [0.6836, 0.7236]** — overlapping
> — at **1.39 against 379.90** dispersion. A near-tie on survival at **273× the
> task quality**.

> Told to maximise survival *alone*, from B1-ternary's own constants, all three
> optimiser seeds walked to the dispersive corner by themselves. The trade-off is
> not an artefact of one hand-designed row.
