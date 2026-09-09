#!/usr/bin/env bash
# Regenerate the experimental record from configs/, appending every invocation
# to docs/run-log.md with the git hash it ran at, the wall time and the output
# path. This is what makes "send me the source of Figure 9" answerable.
#
#   scripts/regenerate_record.sh            run every job, in verification order
#   scripts/regenerate_record.sh JOB [JOB]  run only the named jobs
#
# Jobs are idempotent: re-running one overwrites its output and appends a new
# run-log line. Every run is seeded from (sim.seed, run_index), so a re-run
# reproduces the file bit-for-bit -- scripts/verify_determinism.py checks that.
set -euo pipefail
cd "$(dirname "$0")/.."

SWARM=./target/release/swarm
LOG=docs/run-log.md
PY=".venv/bin/python"
export PYTHONPATH=harness/src

log_line() {  # phase, command, seconds, output
  local size="-"
  [ -f "$4" ] && size="$(du -h "$4" | cut -f1)"
  printf '| %s | `%s` | `%s` | %s | `%s` | %s |\n' \
    "$1" "$(git rev-parse --short HEAD)" "$2" "$(date -u +%Y-%m-%dT%H:%MZ)" "$4" "$3 s / $size" >> "$LOG"
}

run() {  # phase, output-path, command...
  local phase="$1" out="$2"; shift 2
  echo "### $out"
  local t0 t1
  t0=$(date +%s)
  "$@"
  t1=$(date +%s)
  log_line "$phase" "$*" "$((t1 - t0))" "$out"
}

sweep()  { run "$1" "results/$2.jsonl" $SWARM sweep  --config "configs/sweeps/$3.toml" --out "results/$2.jsonl"; }
search() { local phase="$1" name="$2"; shift 2
           run "$phase" "results/$name.json" $SWARM search --out "results/$name.json" "$@"; }

# A derived file: a filtered view of a sweep, kept as its own file because a
# figure script or verify_numbers.py reads it under that name.
derive() {  # phase, out-name, in-name, python-predicate
  local phase="$1" out="results/$2.jsonl" src="results/$3.jsonl" pred="$4"
  local t0 t1; t0=$(date +%s)
  $PY - "$src" "$out" "$pred" <<'EOF'
import json, sys
src, out, pred = sys.argv[1:4]
f = eval("lambda r: " + pred)
n = 0
with open(src) as fh, open(out, "w") as oh:
    for line in fh:
        r = json.loads(line)
        if f({**r, **r.get("cell", {})}):  # sweep coords live under "cell"
            oh.write(line); n += 1
print(f"wrote {n} records to {out}")
EOF
  t1=$(date +%s)
  log_line "$phase" "filter $src -> $out where $pred" "$((t1 - t0))" "$out"
}

# ---------------------------------------------------------------- the manifest
job_validation() {
  sweep "0.2 validation" gauci_scaling              gauci_scaling
  sweep "0.2 validation" link_distance              link_distance_sensitivity
  sweep "0.2 validation" occlusion_shakedown        occlusion_shakedown
  sweep "0.2 validation" small_n_noise_probe        small_n_noise_probe
  sweep "0.2 validation" small_n_start_radius_probe small_n_start_radius_probe
  sweep "0.2 validation" small_n_time_gate          small_n_time_gate
  sweep "0.2 validation" sensor_fov_gate            sensor_fov_gate
  sweep "0.2 validation" timestep_convergence       timestep_convergence
  sweep "0.2 validation" timestep_fov_gate          timestep_fov_gate
}
job_terrain_early() {
  sweep "0.2 terrain"    terrain_idea_a             terrain_idea_a
  sweep "0.2 terrain"    terrain_h1_fine            terrain_h1_fine
  sweep "0.2 terrain"    terrain_h2_r0_scaling      terrain_h2_r0_scaling
  sweep "0.2 terrain"    terrain_h2_powered         terrain_h2_powered
  # theta_m = 1.5 is past the traction floor and outside the model's valid
  # range; the figure and every number in section 13 use the valid subset.
  derive "0.2 terrain"   terrain_h2_powered_valid   terrain_h2_powered \
         "r['terrain.friction_amplitude'] <= 1.0"
  sweep "0.2 terrain"    terrain_mechanism          terrain_mechanism
  sweep "0.2 terrain"    terrain_mechanism_regression terrain_mechanism_regression
  sweep "0.2 terrain"    terrain_h3_capability      terrain_h3_capability
}
job_pursuer() {
  sweep "0.2 pursuer"    pursuer_idea_b             pursuer_idea_b
  sweep "0.2 pursuer"    pursuer_dispersive         pursuer_dispersive
  # The surface figure shows one handling time; the kappa figure shows both.
  derive "0.2 pursuer"   pursuer_dispersive_h1.93   pursuer_dispersive \
         "r['pursuer.handling_time'] == 1.93"
  sweep "0.2 pursuer"    pursuer_pareto             pursuer_pareto
}
job_searches_single() {
  search "0.2 search" search_s2 --config configs/search/train_s2_peak.toml \
         --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000
  search "0.2 search" search_s2_flat --config configs/search/train_s2_flat.toml \
         --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000
  search "0.2 search" search_s4 --config configs/search/train_s4_peak.toml \
         --budget 600 --runs-per-eval 12 --seed 1 --training-seed 900000
  search "0.2 search" search_s4_warm --config configs/search/train_s4_peak.toml \
         --budget 600 --runs-per-eval 12 --seed 1 --training-seed 950000 \
         --init '[-0.285218,-0.949495,0.935379,-0.226159]'
}
job_tuning() {
  sweep "0.2 tuning"     terrain_retune_cost        terrain_retune_cost
  sweep "0.2 tuning"     terrain_warm_s4            terrain_warm_s4
  sweep "0.2 tuning"     terrain_tuning_control     terrain_tuning_control
  sweep "0.2 tuning"     terrain_tuning_control_r15 terrain_tuning_control_r15
}
job_regime() {
  sweep "0.2 regime"     terrain_regime_robustness  terrain_regime_robustness
  sweep "0.2 regime"     terrain_regime_tau         terrain_regime_tau
  sweep "0.2 regime"     terrain_regime_tau_flat    terrain_regime_tau_flat
}
job_lambda() {
  sweep "0.2 lambda"     terrain_lambda_sweep       terrain_lambda_sweep
  sweep "0.2 lambda"     terrain_lambda_collapse    terrain_lambda_collapse
  sweep "0.2 lambda"     terrain_lambda_r0_family   terrain_lambda_r0_family
  sweep "0.2 lambda"     terrain_lambda_r0_family_r074 terrain_lambda_r0_family_r074
  sweep "0.2 lambda"     terrain_lambda_body        terrain_lambda_body
}
job_searches_class() {
  local CLASS=(--class 'swarm.init.radius=0.74,1.5,3.0' --class 'swarm.n=20,50')
  search "0.2 search" search_s2_class_flat --config configs/search/train_s2_class_flat.toml \
         --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 910000 "${CLASS[@]}"
  search "0.2 search" search_s2_class_flat_seed2 --config configs/search/train_s2_class_flat.toml \
         --budget 1200 --runs-per-eval 12 --seed 2 --training-seed 910000 "${CLASS[@]}"
  search "0.2 search" search_s2_class_flat_seed3 --config configs/search/train_s2_class_flat.toml \
         --budget 1200 --runs-per-eval 12 --seed 3 --training-seed 910000 "${CLASS[@]}"
  search "0.2 search" search_s2_class_rough --config configs/search/train_s2_class_rough.toml \
         --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 920000 "${CLASS[@]}"
  # tau varies BETWEEN conditions, so the class is explicit points, not a product.
  search "0.2 search" search_s2_class_rough_tau --config configs/search/train_s2_class_rough_tau.toml \
         --budget 1200 --runs-per-eval 12 --seed 1 --training-seed 920000 \
         --class-point 'swarm.init.radius=0.74,swarm.n=20,sim.duration=600.0' \
         --class-point 'swarm.init.radius=0.74,swarm.n=50,sim.duration=600.0' \
         --class-point 'swarm.init.radius=1.5,swarm.n=20,sim.duration=600.0' \
         --class-point 'swarm.init.radius=1.5,swarm.n=50,sim.duration=600.0' \
         --class-point 'swarm.init.radius=3.0,swarm.n=20,sim.duration=3600.0' \
         --class-point 'swarm.init.radius=3.0,swarm.n=50,sim.duration=3600.0'
}
job_class_eval() {
  sweep "0.2 class"      terrain_class_eval               terrain_class_eval
  sweep "0.2 class"      terrain_class_eval_tau           terrain_class_eval_tau
  sweep "0.2 class"      terrain_class_tau_eval           terrain_class_tau_eval
  sweep "0.2 class"      terrain_class_tau_eval_tau       terrain_class_tau_eval_tau
  sweep "0.2 class"      terrain_class_objective_probe    terrain_class_objective_probe
  sweep "0.2 class"      terrain_class_objective_probe_far terrain_class_objective_probe_far
}
job_phase0_seeds() {
  sweep "0.2 seeds"      phase0_seeds                 phase0_seeds
  sweep "0.2 seeds"      phase0_seeds_tau             phase0_seeds_tau
  sweep "0.2 seeds"      phase0_seeds_objective_probe phase0_seeds_objective_probe
}

ALL=(validation terrain_early pursuer searches_single tuning regime lambda
     searches_class class_eval phase0_seeds)
for job in "${@:-${ALL[@]}}"; do
  echo "======== job $job"
  "job_$job"
done
