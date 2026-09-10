#!/usr/bin/env python3
"""Sample experiment 4's pseudo-realities and generate every config they need.

Pre-registered at `docs/preregistration/pseudo-reality.md`, commit 367ee93. The
sampling seed, the six parameters, their ranges and the order they are consumed
in were all fixed in that file BEFORE this script existed; this script only
executes the draw, so that the model family is reproducible from the seed rather
than transcribed from a table someone typed.

    python scripts/build_pseudo_reality_configs.py            write the configs
    python scripts/build_pseudo_reality_configs.py --check    fail if any is stale
    python scripts/build_pseudo_reality_configs.py --table    the model table only

Following Ligot & Birattari (2020), the models perturb *implementation* choices
around the design point — actuation noise, sensor dropout, contact solver effort,
timestep — and NOT the physics being modelled. The kinematics, the traction model,
the pursuer's lock-on law and the sensor geometry are identical in every model. A
result robust across this family is robust to how carefully the simulator is
integrated and how noisy its sensors are, **not** to whether the model is right.
That is the main way this experiment can be over-claimed and the wording is fixed
here as well as in the findings.

WHAT IS GENERATED, and why it is this shape. The pre-registration allowed a
single `pseudo_reality.toml` with a file-valued axis if the sweep machinery
supported one, and named one-config-per-model as the fallback. It does not: a
sweep's `base` is a single path resolved once (`main.rs`, `base_path`), and axes
carry values for ONE config path, so a whole model cannot be an axis value.
The fallback is therefore what runs, and it is recorded in the findings as such.

  configs/pseudo_reality/model_01.toml .. model_10.toml
      one full base config per sampled model: gauci_baseline.toml with exactly
      the six sampled parameters replaced. Model 00 is the unperturbed reference
      and IS gauci_baseline.toml — it gets no file of its own, because a copy of
      the baseline that could drift from the baseline is worse than no copy.

  configs/pseudo_reality/aggregation_model_XX.toml   (00..10)
  configs/pseudo_reality/pursuit_model_XX.toml       (00..10)
      the two comparison groups, rows copied verbatim from the configs that
      already carry those constants. Only `base` differs between the eleven
      copies of each.

They live in configs/pseudo_reality/ rather than configs/sweeps/ so that
twenty-two generated files do not swamp the directory where every file is a
hand-written experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "configs" / "pseudo_reality"
BASELINE = REPO / "configs" / "gauci_baseline.toml"

SEED = 20260910          # pre-registered in docs/preregistration/pseudo-reality.md
K = 10                   # sampled models; model 00 is the unperturbed reference

# The parameter table, in the order the pre-registration lists it, which is the
# order the generator consumes the stream in. Changing either the order or a
# range changes the draw, so neither may be touched without a new registration.
PARAMS = [
    ("noise.wheel_noise",       "uniform", (0.00, 0.05),  0.00),
    ("occlusion.fn_rate",       "uniform", (0.00, 0.10),  0.00),
    ("occlusion.fp_rate",       "uniform", (0.00, 0.02),  0.00),
    ("sim.collision_iterations", "choice", (8, 16, 32),   32),
    ("sim.contact_tolerance",   "uniform", (5e-6, 2e-5),  1e-5),
    ("sim.dt",                   "choice", (0.05, 0.10),  0.10),
]


def sample() -> list[dict]:
    """The draw. One model at a time, six parameters in table order.

    The alternative reading — ten draws of parameter 1, then ten of parameter 2 —
    would give a different family from the same seed. Model-major is the reading
    the pre-registration's phrase "each parameter drawn uniformly and
    independently ... in the order the table lists" most naturally carries, and
    it is fixed here so the family is reproducible either way it is read later.
    """
    rng = np.random.default_rng(SEED)
    models = []
    for _ in range(K):
        m = {}
        for path, kind, spec, _default in PARAMS:
            if kind == "uniform":
                m[path] = float(rng.uniform(*spec))
            else:
                m[path] = spec[int(rng.integers(0, len(spec)))]
        models.append(m)
    return models


def fmt(path: str, value) -> str:
    if path == "sim.collision_iterations":
        return str(int(value))
    if path == "sim.contact_tolerance":
        return f"{value:.6e}"
    return f"{value:.6f}"


# --------------------------------------------------------------- model bases --
def model_base(i: int, m: dict) -> str:
    """gauci_baseline.toml with exactly the six sampled parameters replaced.

    Generated from the baseline rather than copied by hand, so `--check` fails if
    the baseline ever moves and these are not regenerated with it.
    """
    text = BASELINE.read_text()
    lines = text.split("\n")
    section = None
    seen: set[str] = set()
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
        elif "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=")[0].strip()
            dotted = f"{section}.{key}" if section else key
            if dotted in m:
                # The baseline's prose above this line still describes the
                # BASELINE ("Clean arena", "Flat board", "Zero here"), and after
                # substitution it would quietly contradict the value. Mark every
                # perturbed line rather than deleting a comment that is correct
                # about the file this was generated from.
                default = next(d for pth, _k, _s, d in PARAMS if pth == dotted)
                out.append(f"{key} = {fmt(dotted, m[dotted])}"
                           f"  # PERTURBED, baseline {fmt(dotted, default)}"
                           f" -- the comment above describes the baseline")
                seen.add(dotted)
                continue
        out.append(line)
    # Parameters the baseline never spells out (it relies on the Rust defaults)
    # are appended to their section rather than left at the default.
    missing = [p for p in m if p not in seen]
    for dotted in missing:
        sec, key = dotted.rsplit(".", 1)
        default = next(d for pth, _k, _s, d in PARAMS if pth == dotted)
        line = (f"{key} = {fmt(dotted, m[dotted])}"
                f"  # PERTURBED, baseline {fmt(dotted, default)} (a Rust default"
                f" the baseline does not spell out)")
        idx = next((j for j, l in enumerate(out) if l.strip() == f"[{sec}]"), None)
        if idx is None:
            out += ["", f"[{sec}]", line]
            continue
        j = idx + 1
        while j < len(out) and not out[j].strip().startswith("["):
            j += 1
        while j > idx + 1 and not out[j - 1].strip():
            j -= 1
        out.insert(j, line)

    header = [
        f"# PSEUDO-REALITY MODEL {i:02d} — freeze lift 1, experiment 4.",
        "#",
        "# GENERATED by scripts/build_pseudo_reality_configs.py from",
        "# configs/gauci_baseline.toml. Edit that script, not this file.",
        "#",
        f"# Drawn from numpy.random.default_rng({SEED}), the sampling seed recorded in",
        "# docs/preregistration/pseudo-reality.md BEFORE the draw. Six parameters,",
        "# consumed in the order that file's table lists them, model-major:",
        "#",
    ]
    for path, _kind, _spec, default in PARAMS:
        header.append(f"#   {path:26s} {fmt(path, m[path]):>14s}   (default {fmt(path, default)})")
    header += [
        "#",
        "# Everything else -- kinematics, traction model, pursuer lock-on law, sensor",
        "# geometry -- is the baseline's and is identical in every model. This family",
        "# perturbs how carefully the simulator is integrated and how noisy its sensors",
        "# are, NOT whether the model is right.",
        "#",
        "# Below this line the file is configs/gauci_baseline.toml verbatim, comments",
        "# included, with the six lines above substituted. Those comments describe the",
        "# BASELINE, so every substituted line is marked `# PERTURBED` -- read the",
        "# marker, not the prose above it.",
        "# " + "-" * 74,
        "",
    ]
    return "\n".join(header) + "\n".join(out)


# -------------------------------------------------------------- sweep configs --
AGG_ROWS = """
[[rows]]
label = "S2-gauci"
# the enumerated reference; the only tight minimum here
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary"
controller = { kind = "gauci", constants = [-0.7, -1.0, 1.0, -1.0], provenance = "enumerated" }

[[rows]]
label = "S2-class-flat-s1"
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.432983, -0.882043] },
  { wheels = [0.792395, -0.886538] },
] }

[[rows]]
label = "S2-class-flat-s2"
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.542573, -0.980003] },
  { wheels = [0.946660, -0.811344] },
] }

[[rows]]
label = "S2-class-flat-s3"
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.409734, -0.752740] },
  { wheels = [0.732649, -0.606024] },
] }

[[rows]]
label = "S2-searched"
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.285218, -0.949495] },
  { wheels = [0.935379, -0.226159] },
] }

[[rows]]
label = "S4-terrain"
[rows.overrides]
"terrain.correlation_length" = 0.1
"sensor.encoding" = "binary_with_terrain"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.236416, -0.519837] },
  { wheels = [0.797842, -0.406434] },
  { wheels = [-0.186302, -0.965739] },
  { wheels = [0.930956, -0.450512] },
] }
"""

PURSUIT_ROWS = """
[[rows]]
label = "B0-blind"
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "binary"
controller = { kind = "gauci", constants = [-0.7, -1.0, 1.0, -1.0], provenance = "enumerated" }

[[rows]]
label = "B1-ternary"
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "ternary"
controller = { kind = "table", memory_bits = 0, provenance = "hand_designed", entries = [
  { wheels = [-0.700000, -1.000000] },
  { wheels = [1.000000, -1.000000] },
  { wheels = [-1.000000, -1.000000] },
] }

[[rows]]
label = "D-dispersive"
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "ternary"
controller = { kind = "table", memory_bits = 0, provenance = "hand_designed", entries = [
  { wheels = [-0.950000, -1.000000] },
  { wheels = [-0.950000, -1.000000] },
  { wheels = [-1.000000, -1.000000] },
] }

[[rows]]
label = "S3-survival_task-s1"
# verbatim from configs/sweeps/pursuer_searched_s3.toml, itself generated from
# results/search_s3_pursuer_survival_task_seed1.json (objective 0.6804).
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "ternary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.494437, -0.920861] },
  { wheels = [0.606990, -0.846642] },
  { wheels = [-0.851754, -0.811688] },
] }

[[rows]]
label = "S3-survival_task-s2"
# objective 0.6608, optimiser seed 2 -- the row Phase 2's rule (a) fired on.
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "ternary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.322343, -0.907322] },
  { wheels = [0.645929, -0.838092] },
  { wheels = [-0.856845, -0.813846] },
] }

[[rows]]
label = "S3-survival_task-s3"
# objective 0.4581 -- the stalled seed. It is here because best-of-three is per
# cell and dropping the weakest draw is exactly the selection section 21 forbids.
[rows.overrides]
"sim.duration" = 120.0
"pursuer.speed_ratio" = 1.5
"pursuer.confusion_radius" = 0.5
"sensor.encoding" = "ternary"
controller = { kind = "table", memory_bits = 0, provenance = "optimiser_found", entries = [
  { wheels = [-0.669710, 0.445321] },
  { wheels = [0.154507, 0.385710] },
  { wheels = [-0.479232, -0.545974] },
] }
"""


def base_ref(i: int) -> str:
    return "../gauci_baseline.toml" if i == 0 else f"model_{i:02d}.toml"


def aggregation_config(i: int) -> str:
    return f'''# PSEUDO-REALITY, comparisons 1 and 2 — model {i:02d}{" (UNPERTURBED REFERENCE)" if i == 0 else ""}.
#
# Pre-registered at docs/preregistration/pseudo-reality.md, commit 367ee93.
# GENERATED by scripts/build_pseudo_reality_configs.py — edit that, not this.
#
# Comparison 1, the terrain tax: S2-gauci against best-of-three S2-class-flat,
# per §21's branch (b), as the paired hold ratio for each row and the paired
# DIFFERENCE between them at theta_m = 0.9.
# Comparison 2, capability flatness: S2-searched † against S4-terrain †, as the
# paired hold-ratio difference at the worst cell. Comparison 2 stays at n = 20 on
# review -- the only n at which A1 is graded SUPPORTED.
#
# theta_m = 0 is the paired flat-ground denominator, not a data point. Runs pair
# WITHIN a model by run index; they are NOT paired across models, because dt and
# collision_iterations differ between models and the same seed does not produce
# the same trajectory. Pretending otherwise would be false pairing.

name = "pseudo-reality-aggregation-model-{i:02d}"
base = "{base_ref(i)}"
runs_per_cell = 100

[[axis]]
path = "terrain.friction_amplitude"
values = [0.0, 0.9]
{AGG_ROWS}'''


def pursuit_config(i: int) -> str:
    return f'''# PSEUDO-REALITY, comparisons 3, 4 and 5 — model {i:02d}{" (UNPERTURBED REFERENCE)" if i == 0 else ""}.
#
# Pre-registered at docs/preregistration/pseudo-reality.md, commit 367ee93.
# GENERATED by scripts/build_pseudo_reality_configs.py — edit that, not this.
#
# Comparison 3, confusion through aggregation: the kappa-response ratio of
#   B0-blind, B1-ternary ‡ and D-dispersive ‡ at r_p = 0.35 m.
# Comparison 4, matched-pair ordering: B1 against D at each r_p, pooled over
#   kappa.
# Comparison 5 (D1): best-of-three searched S = 3 † against B0 AND against B1, at
#   comparison 4's cells. Two references, because experiment 1 split G4 in two:
#   the comparison against B0 is the capability claim that goes in the abstract,
#   the one against B1 is the regime-specific claim.
#
# h = 1.93 s throughout, as every comparison specifies. Survival is read as MEAN
# PER-ROBOT survival with a Wilson interval (§12.1 D0), never as a median of
# survival_fraction.

name = "pseudo-reality-pursuit-model-{i:02d}"
base = "{base_ref(i)}"
runs_per_cell = 100

[[axis]]
path = "pursuer.range"
values = [0.1, 0.35, 1.0]

[[axis]]
path = "pursuer.confusion"
values = [0.0, 5.0]

[[axis]]
path = "pursuer.handling_time"
values = [1.93]
{PURSUIT_ROWS}'''


def targets(models: list[dict]) -> dict[pathlib.Path, str]:
    out: dict[pathlib.Path, str] = {}
    for i, m in enumerate(models, start=1):
        out[OUT / f"model_{i:02d}.toml"] = model_base(i, m)
    for i in range(0, K + 1):
        out[OUT / f"aggregation_model_{i:02d}.toml"] = aggregation_config(i)
        out[OUT / f"pursuit_model_{i:02d}.toml"] = pursuit_config(i)
    return out


def table(models: list[dict]) -> str:
    head = "| model | " + " | ".join(p for p, *_ in PARAMS) + " |"
    rule = "|---" * (len(PARAMS) + 1) + "|"
    rows = ["| 00 *(reference)* | " +
            " | ".join(f"**{fmt(p, d)}**" for p, _k, _s, d in PARAMS) + " |"]
    for i, m in enumerate(models, start=1):
        rows.append(f"| {i:02d} | " + " | ".join(fmt(p, m[p]) for p, *_ in PARAMS) + " |")
    return "\n".join([head, rule] + rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if any generated file differs from what "
                         "this script would write now")
    ap.add_argument("--table", action="store_true", help="print the model table and stop")
    args = ap.parse_args()

    models = sample()
    if args.table:
        print(table(models))
        return 0

    want = targets(models)
    if args.check:
        bad = []
        for path, text in want.items():
            if not path.exists():
                bad.append(f"missing {path.relative_to(REPO)}")
            elif path.read_text() != text:
                bad.append(f"stale   {path.relative_to(REPO)}")
        if bad:
            print("\n".join(bad), file=sys.stderr)
            print(f"\n{len(bad)} of {len(want)} generated configs are not what the "
                  "generator would write. Re-run without --check.", file=sys.stderr)
            return 1
        print(f"all {len(want)} generated configs are current")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for path, text in want.items():
        path.write_text(text)
    digest = hashlib.sha256("".join(want[p] for p in sorted(want)).encode()).hexdigest()[:16]
    print(f"wrote {len(want)} configs to {OUT.relative_to(REPO)}  (sha256:{digest})")
    print()
    print(table(models))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
