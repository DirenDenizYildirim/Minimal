# Roadmap

Build doc §6, mapped onto this repository. The schedule there is for a team of
three; solo, multiply by ~2.5 and drop the hardware track until Paper 1 is
submitted.

| Weeks | Build doc | Repository state |
|---|---|---|
| 1–3 | Tier-1 sim; reproduce Gauci constants and scaling. **Gate.** | Done. **Gate passed**, with the small-n criterion corrected — see `docs/validation.md` and ADR 0005. |
| 3 | Occlusion shakedown | `configs/sweeps/occlusion_shakedown.toml`, M0 vs M1-hysteresis. Runs; re-run once the gate passes. |
| 4–7 | Terrain generator; Idea A sweep; H2 against `R0`; anisotropy lemma | Terrain model, dials and the two-dial surface done. **H1 tested three ways and null** — needs revising in the build doc. **H2 partially supported**: the effect vanishes for λ > R₀, but the sweep was under-powered to locate a transition. H3 (slope-sensor row) and the anisotropy lemma not started. |
| 7–11 | Pursuer family; Idea B rows; capture-rate surfaces | `pursuer.rs` holds parameters only. Sensor already returns `AgentKind::Pursuer` and the S = 3 / S = 5 encodings for rows B1–B4 are implemented and tested. |
| 11–15 | ARGoS cells; hardware | Not started. |
| 15+ | Write Paper 1 | — |

## Next actions, in order

1. **Idea A, H2, properly powered.** The first sweep showed terrain does nothing
   once λ > R₀ — H2's substantive claim — but could not locate a *transition*,
   because at θ_m ≤ 0.4 aggregation never actually fails. Re-run with θ_m pushed
   to 0.6–1.0, and separate λ/R₀ from λ/ℓ by varying the axle length
   independently of the wheel constants (both are config fields, so this costs
   only runs). Only then fit the transition. Details in `docs/findings.md` §4.
2. **Revise H1 in the build doc.** Three independent null results
   (`docs/findings.md` §3). The Daymude analogy was over-extended: their noise
   breaks a *contact deadlock* in a discrete model, and this continuous model has
   no such deadlock. This is a doc change, not more runs.
3. **Idea A, H3.** Needs a slope-detecting sensor state (S = 4: binary LOS × a
   tilt bit), plus the eight-constant row that goes with it.
4. **Idea B.** Implement the pursuer step — search phase under finite `r_p`,
   `p_lock = 1/(1 + κ·n_local)`, the three targeting rules — and switch the
   primary metric to capture rate per unit time, normalised by swarm size.
5. **Week-3 shakedown, finish the job.** The hand-written hysteresis row showed a
   consistent gain, so run the eight-constant search it was meant to justify.
6. Fold the impossibility result into the framing (`docs/literature-corrections.md`),
   since `c*(θ)` now has to be a function of swarm size as well as environment.

## Deliberately deferred

* **Bounded arenas.** Refused by config validation. In a bounded arena on a
  slope the downhill wall aggregates the swarm for us, which would make the
  Idea A result an artefact.
* **Arithmetic controllers (`A = 1`).** Everything in Ideas A and B is a lookup
  table. The flag exists in the capability vector so the accounting is honest.
* **Communication (`K > 0`).** The plumbing is in the controller table and the
  step loop; row B4 is what turns it on. It is counted in `K`, not treated as
  free sensing.
