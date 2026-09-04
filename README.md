# Minimal Swarms in Hostile Environments

> Minimalist swarm robotics asks "what is the least sensing, compute and memory
> that produces behaviour X?" — and answers it in flat, uniform, unthreatened
> arenas. This project measures how that minimum **moves** under environmental
> hostility. **Capability is the dependent variable; the environment is the
> independent one.**

The plan this repository implements is [`docs/build-doc-v2.md`](docs/build-doc-v2.md).

## The idea in one figure

For each capability row `c = (S, M, A, K)`, plot the performance surface over
the hostility dials, then draw the threshold contours `P = T` on it. Several
contours on one panel (T = 0.7, 0.8, 0.9) show how the "minimum" depends on
where the bar is set. The frontier `c*(θ)` is read off as the lowest row whose
contour still encloses θ.

`c = (S, M, A, K)` is **sensor states** (not bits), **memory bits**, an
**arithmetic** flag, and **communication bits broadcast per step**. It is a set
of vectors, not a chain of supersets — two extra sensor states and one memory
bit are incomparable, and nothing here pretends otherwise.

## Layout

```
crates/swarm-core/    Tier-1 simulator: kinematics, sensor, controllers, dials, metrics
crates/swarm-cli/     `swarm` binary: describe / run / sweep
harness/              Python: aggregation, bootstrap CIs, surfaces with contours
configs/              Baseline config and sweep files (the experiments themselves)
docs/                 Build doc, validation gates, decision records
results/  figures/    Generated; not committed. Regenerate from configs.
```

## Quickstart

```bash
# Simulator
cargo test                                                    # 64 tests
cargo build --release

# What does this config actually cost, in capability terms?
./target/release/swarm describe --config configs/gauci_baseline.toml

# 30 trials of the clean-arena baseline
./target/release/swarm run --config configs/gauci_baseline.toml --runs 30 \
  --out results/baseline.jsonl

# A sweep: capability rows crossed with a grid of hostility dials
./target/release/swarm sweep --config configs/sweeps/occlusion_shakedown.toml \
  --out results/occlusion.jsonl

# Analysis
uv venv .venv && uv pip install --python .venv/bin/python -e harness
PYTHONPATH=harness/src .venv/bin/python -m swarm_harness.cli \
  table results/occlusion.jsonl --by row occlusion.fn_rate --metric final_dispersion
```

`swarm sweep --dry-run` validates every cell and reports the workload without
simulating anything.

### Regenerating a figure

Results and figures are not committed — they are reproducible from the configs,
and every run is seeded from `(sim.seed, run_index)`:

```bash
./target/release/swarm sweep --config configs/sweeps/terrain_idea_a.toml \
  --out results/terrain_idea_a.jsonl
PYTHONPATH=harness/src .venv/bin/python -m swarm_harness.cli surface \
  results/terrain_idea_a.jsonl \
  --x terrain.slope_angle --y terrain.friction_amplitude \
  --metric fraction_time_single_cluster --thresholds 0.5 0.6 0.7 \
  --out figures/terrain_idea_a_surface.png
```

## What is implemented

| Piece | Status |
|---|---|
| Differential-drive kinematics, exact arc integration | done |
| Line-of-sight sensor: binary / ternary / ternary-with-side (S = 2, 3, 5) | done |
| Lookup-table controllers over `(S, M, A, K)`, with provenance | done |
| Occlusion dial `θ_occ` — correlated false negatives and positives | done |
| Actuation-noise dial (a robot property, not a hostility dial; off by default) | done |
| Terrain dial `θ_terr` — per-wheel traction field, heading-dependent gravity | done |
| Dispersion and cluster metrics, in the centroid frame | done |
| Sweep harness, JSONL output, surfaces with threshold contours | done |
| Pursuer dial `θ_pred` (Idea B) | **parameters only** — a config that sets one is refused, not ignored |
| PFSM / automatic design (Idea C) | not started |
| Transient sensor + latch (Idea D) | not started |
| Tier 2 (ARGoS), hardware track | not started |

## Status: the week-1 gate has passed

The build doc puts a gate before any hostility dial is added — reproduce Gauci's
aggregation and its scaling in swarm size.

**Verified against the sources.** The e-puck model (disk of diameter 7.4 cm,
inter-wheel distance 5.1 cm, wheel speeds in ±12.8 cm/s), the sensor (a
zero-width ray cast from the robot's front, taking the first body it intersects,
infinite range), the control cycle (0.1 s), and the controller
x* = (−0.7, −1, 1, −1). Together these reproduce all three of the paper's derived
quantities — turn radius 14.45 cm, ω₀ = 0.75 rad/s, ω₁ = 5.02 rad/s — and a test
pins them. That check is what caught the inter-wheel distance being 5.3 cm
instead of 5.1.

Aggregation reproduces for n ≥ 10: dispersion falls from ~19 to 1.15 at n = 100,
against ~1 for a perfectly packed cluster.

**The small-n row took five wrong hypotheses to close**, and the answer was that
the check was wrong, not the simulator. It appealed to Gauci's two-robot
theorem — which [Steinberg & Solovey (2024)](https://arxiv.org/abs/2501.00390)
have since **disproven**, reporting the same controller failing on 4.24% of
two-robot trials. And the literature scores aggregation as *reaching* a connected
configuration, not being in one at τ. For a pair that is an order of magnitude:
93% of pairs here reach exact contact, ~10% are still touching at τ. Measured the
way the literature measures it, this simulator agrees with it.

Ruled out along the way, each with a committed sweep: angular aliasing, the time
budget (flat to τ = 48 000 s), missing actuation noise, initial separation, and
timestep discretisation (flat over a 50-fold range). Three are useful
sensitivity results in their own right.

The same paper proves something the build doc does not yet cite: **no bimodal
controller in this class aggregates for every swarm size.** That sharpens the
project's framing rather than undermining it — see
[`docs/literature-corrections.md`](docs/literature-corrections.md).

Full record: [`docs/validation.md`](docs/validation.md). Experimental results so
far: [`docs/findings.md`](docs/findings.md). Schedule:
[`docs/roadmap.md`](docs/roadmap.md).

## Two rules this repository enforces in code

**Minima are upper bounds unless the search was exhaustive.** Every controller
carries a `provenance`. Only `enumerated` rows report a tight minimum; every
other row is stamped as an upper bound in the CLI output, in the run records,
and on the figures. An unlabelled controller defaults to the pessimistic
assumption. "No controller found meeting T" means *not found*, not *not
possible*.

**A dial that is not implemented is refused, not ignored.** Configuring a
pursuer today produces an error, not a pursuer-free run under a pursuer
filename.

## Citation and prior art

The baseline is Gauci, Chen, Li, Dodd & Groß (2014), IJRR, *Self-organized
aggregation without computation* — one binary sensor, no memory, no arithmetic,
four wheel constants found by exhaustive grid search. Its constants are the only
tight minimum in this repository. `docs/build-doc-v2.md` §1 and §8 carry the full
reading list, including the prior art a reviewer will name (BEECLUST, which puts
non-uniformity in the *target* rather than as a perturbation; the pursuit-evasion
survey; predator confusion; Berg & Purcell on temporal versus spatial sensing).
