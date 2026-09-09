# Run log

Every `swarm sweep`, `swarm search`, figure script and verification command that
produced a file in `results/` or `figures/`, with the git hash it ran at, when it
ran, the wall time and the output path.

`results/` and `figures/` are generated and not committed (README). This file is
what makes them recoverable: it is the answer to "send me the source of Figure 9".

**How to read a row.** The command is literal — copy it and it runs. Sweeps and
searches go through `scripts/regenerate_record.sh`, which is the same commands
with the logging attached; `scripts/regenerate_record.sh <job>` re-runs one group.
Every run is seeded from `(sim.seed, run_index)`, so a re-run reproduces the file
bit-for-bit; `scripts/verify_determinism.py` is the check that it does.

Wall time is on a 4-core machine unless a row says otherwise, and "size" is the
output file on disk.

## Environment

| item | value |
|---|---|
| host | 4 cores, 15 GB RAM, Linux 6.18 |
| rustc / cargo | see `rust-toolchain.toml` (pinned) |
| Python | 3.11, `uv venv .venv && uv pip install --python .venv/bin/python -e 'harness[stats]'` |
| binary | `cargo build --release` → `target/release/swarm` |
| figure scripts | `PYTHONPATH=harness/src .venv/bin/python harness/figures_<name>.py` |

## Freeze lift 1 — Phase 0: regenerating the frozen record

The evidence base was frozen at `ce427a8`. `results/` and `figures/` are not
committed, so Phase 0 regenerates every file `scripts/verify_numbers.py` and the
§10 figure inventory refer to, and checks them against `docs/paper-source.md` §13.

### Workload, from `--dry-run` before anything ran

| group | trials | robot-timesteps | est. core-hours |
|---|---|---|---|
| all 40 sweep configs | 146 910 | 25.5 × 10⁹ | 9.8 |
| 9 searches (4 single-condition, 5 class) | 122 400 | ~30 × 10⁹ | ~11 |
| **Phase 0 total** | **269 310** | **~55 × 10⁹** | **~21** |

Measured throughput used for the estimate: 725 000 robot-timesteps per
core-second (800 trials of `terrain_warm_s4` in 33.6 s wall / 132.5 core-s).

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
