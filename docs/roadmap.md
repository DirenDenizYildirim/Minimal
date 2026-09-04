# Roadmap

Build doc §6, mapped onto this repository. The schedule there is for a team of
three; solo, multiply by ~2.5 and drop the hardware track until Paper 1 is
submitted.

| Weeks | Build doc | Repository state |
|---|---|---|
| 1–3 | Tier-1 sim; reproduce Gauci constants and scaling. **Gate.** | Done. **Gate passed**, with the small-n criterion corrected — see `docs/validation.md` and ADR 0005. |
| 3 | Occlusion shakedown | `configs/sweeps/occlusion_shakedown.toml`, M0 vs M1-hysteresis. Runs; re-run once the gate passes. |
| 4–7 | Terrain generator; Idea A sweep; H2 against `R0`; anisotropy lemma | Terrain model, dials and the two-dial surface done. **H1 tested three ways and null** — needs revising in the build doc. **H2 supported**: the peak sits at λ/R₀ ≈ 0.7 across a 4× axle range; varying R₀ moves it 560%, varying the axle 5%. H3 (slope-sensor row) and the anisotropy lemma not started. |
| 7–11 | Pursuer family; Idea B rows; capture-rate surfaces | **Implemented**: search phase under finite `r_p`, `p_lock = 1/(1 + κ·n_local)`, three targeting rules, Holling handling time, capture accounting. Rows B0–B3 in `configs/sweeps/pursuer_idea_b.toml` with hand-designed tables. **B4 blocked** on communication (`rx` is held at 0). |
| 11–15 | ARGoS cells; hardware | Not started. |
| 15+ | Write Paper 1 | — |

## Next actions, in order

1. **Wire communication, then add row B4.** It is the only Idea B row missing,
   and the only one that exercises `K`. The controller table already has an rx
   axis and the step loop already carries a tx value; what is missing is
   delivering one robot's tx to its neighbours' rx. Decide the delivery model
   first — broadcast radius, or line-of-sight only — because that choice is
   itself a capability claim and has to be counted honestly in `K`.
2. **Search the eight constants for the M1 row.** The hand-written hysteresis
   controller beat Gauci's at every dropout rate (`docs/findings.md` §1), which
   was what the week-3 shakedown existed to establish. The search itself is the
   Idea C machinery, so this is the natural bridge into Paper 2.
3. **The anisotropy lemma.** H2 now says what the bound should depend on: λ/R₀,
   worst near 0.7. That is a much narrower target than the build doc started
   with.
4. **Idea A, H3.** Needs a slope-detecting sensor state (S = 4: binary LOS × a
   tilt bit), plus the eight-constant row that goes with it.
5. **Revise H1 and the citations in the build doc** — collected in
   `docs/literature-corrections.md`. Doc changes, not runs.

## Deliberately deferred

* **Bounded arenas.** Refused by config validation. In a bounded arena on a
  slope the downhill wall aggregates the swarm for us, which would make the
  Idea A result an artefact.
* **Arithmetic controllers (`A = 1`).** Everything in Ideas A and B is a lookup
  table. The flag exists in the capability vector so the accounting is honest.
* **Communication (`K > 0`).** The plumbing is in the controller table and the
  step loop; row B4 is what turns it on. It is counted in `K`, not treated as
  free sensing.
