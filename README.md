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

## What is implemented

| Piece | Status |
|---|---|
| Differential-drive kinematics, exact arc integration | done |
| Line-of-sight sensor: binary / ternary / ternary-with-side (S = 2, 3, 5) | done |
| Lookup-table controllers over `(S, M, A, K)`, with provenance | done |
| Occlusion dial `θ_occ` — correlated false negatives and positives | done |
| Terrain dial `θ_terr` — per-wheel traction field, heading-dependent gravity | done |
| Dispersion and cluster metrics, in the centroid frame | done |
| Sweep harness, JSONL output, surfaces with threshold contours | done |
| Pursuer dial `θ_pred` (Idea B) | **parameters only** — a config that sets one is refused, not ignored |
| PFSM / automatic design (Idea C) | not started |
| Transient sensor + latch (Idea D) | not started |
| Tier 2 (ARGoS), hardware track | not started |

See [`docs/roadmap.md`](docs/roadmap.md) for the schedule this maps onto and
[`docs/validation.md`](docs/validation.md) for what has been verified — including
a gate that has **not** yet passed.

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
