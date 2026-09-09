#!/usr/bin/env bash
# Regenerate every figure in `docs/paper-source.md` §10 from a committed script,
# appending each invocation to docs/run-log.md.
#
#   scripts/regenerate_figures.sh                every figure
#   scripts/regenerate_figures.sh figures_pareto.py [...]   only these scripts
#
# There are no `swarm-figure` CLI invocations here, by design. Eleven of the §10
# figures were attributed to that CLI with only the subcommand recorded and none
# of its arguments (verification-report D9), so they could not be regenerated at
# all; each now has a script, and this file is how they are run.
set -euo pipefail
cd "$(dirname "$0")/.."

LOG=docs/run-log.md
export PYTHONPATH=harness/src
PY=.venv/bin/python

# Scripts in the order their sections appear, so a partial run still leaves a
# readable prefix of the inventory.
SCRIPTS=(
  figures_gauci_scaling.py            # validation §1
  figures_occlusion_shakedown.py      # §1   (curve + surface)
  figures_terrain_idea_a.py           # §2   (surface + curve)
  figures_terrain_h2.py               # §4   (powered + r0_scaling)
  figures_terrain_mechanism.py        # §6
  figures_terrain_h3_capability.py    # §7
  figures_terrain_retune_cost.py      # §9 + §10 (retune + warm)
  figures_mechanism_regression.py     # §11
  figures_pareto.py                   # §12
  figures_tuning_control.py           # §13
  figures_decision_rule_regimes.py    # §13 + §14
  figures_regime_robustness.py        # §14
  figures_lambda_sweep.py             # §15
  figures_lambda_collapse.py          # §16
  figures_lambda_r0_family.py         # §17
  figures_lambda_body.py              # §18
  figures_idea_b.py                   # §5 + §8 (first_pass + dispersive)
  figures_class_search.py             # §19
  figures_class_tau.py                # §20
  figures_seed_reproducibility.py     # §21
)

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

for s in "${@:-${SCRIPTS[@]}}"; do
  echo "======== $s"
  t0=$(date +%s)
  # Combined output to a file rather than through a pipeline: a script that
  # names no PNG on stdout (figures_mechanism_regression prints only "ok") makes
  # `grep` exit 1, and under `pipefail` that would abort the whole run.
  $PY "harness/$s" > "$TMP/out" 2>&1
  t1=$(date +%s)
  cat "$TMP/out"
  out=$(grep -oE 'figures/[a-z0-9_]+\.png' "$TMP/out" | sort -u | tr '\n' ' ' || true)
  # Fall back to whatever the script's own savefig calls name, so a script that
  # prints nothing still gets its outputs recorded.
  [ -n "$out" ] || out=$(grep -oE 'figures/[a-z0-9_]+\.png' "harness/$s" | sort -u | tr '\n' ' ')
  printf '| 0.4 figures | `%s` | `PYTHONPATH=harness/src .venv/bin/python harness/%s` | `%s` | %s | %s s |\n' \
    "$(git rev-parse --short HEAD)" "$s" "$(date -u +%Y-%m-%dT%H:%MZ)" \
    "$(for f in $out; do printf '`%s` ' "$f"; done)" "$((t1 - t0))" >> "$LOG"
done
