# Roadmap

Build doc §6, mapped onto this repository. The schedule there is for a team of
three; solo, multiply by ~2.5 and drop the hardware track until Paper 1 is
submitted.

| Weeks | Build doc | Repository state |
|---|---|---|
| 1–3 | Tier-1 sim; reproduce Gauci constants and scaling. **Gate.** | Simulator, CLI, sweep harness and metrics done. `configs/sweeps/gauci_scaling.toml`. **Gate not yet passed** — see `docs/validation.md`. |
| 3 | Occlusion shakedown | `configs/sweeps/occlusion_shakedown.toml`, M0 vs M1-hysteresis. Runs; re-run once the gate passes. |
| 4–7 | Terrain generator; Idea A sweep; H2 against `R0`; anisotropy lemma | Terrain model and dials done and tested. `configs/sweeps/terrain_idea_a.toml`. H2's `R0` sweep and the H3 slope-sensor row are not written yet. |
| 7–11 | Pursuer family; Idea B rows; capture-rate surfaces | `pursuer.rs` holds parameters only. Sensor already returns `AgentKind::Pursuer` and the S = 3 / S = 5 encodings for rows B1–B4 are implemented and tested. |
| 11–15 | ARGoS cells; hardware | Not started. |
| 15+ | Write Paper 1 | — |

## Next actions, in order

1. **Close the week-1 gate.** n = 2 does not aggregate; the diagnosis and the
   candidate fix are in `docs/validation.md`. Nothing downstream is trustworthy
   until this is closed, because every hostility result is a comparison against
   the clean-arena baseline.
2. Re-run the occlusion shakedown at the settled timestep and sensor model.
3. Idea A: add the H2 companion sweep (vary the four wheel constants, and hence
   `R0`, at fixed correlation length `λ`; check the transition tracks `R0` rather
   than swarm size). Add the H3 row, which needs a slope-detecting sensor state.
4. Idea B: implement the pursuer step — search phase under finite `r_p`,
   `p_lock = 1/(1 + κ·n_local)`, the three targeting rules — and switch the
   primary metric to capture rate per unit time, normalised by swarm size.

## Deliberately deferred

* **Bounded arenas.** Refused by config validation. In a bounded arena on a
  slope the downhill wall aggregates the swarm for us, which would make the
  Idea A result an artefact.
* **Arithmetic controllers (`A = 1`).** Everything in Ideas A and B is a lookup
  table. The flag exists in the capability vector so the accounting is honest.
* **Communication (`K > 0`).** The plumbing is in the controller table and the
  step loop; row B4 is what turns it on. It is counted in `K`, not treated as
  free sensing.
