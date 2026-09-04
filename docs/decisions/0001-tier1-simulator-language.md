# 0001 — Tier-1 simulator in Rust, analysis in Python

**Status:** accepted, 2026-09-04.

## Context

The build doc (§4) says to decide the Tier-1 language up front and gives the
constraint: pairwise line-of-sight with ray checks is O(n²) per step, and NumPy
will not reach 10⁵–10⁶ runs at n = 50. The two options offered are Rust
(rayon over runs) or a vectorised GPU sim (JAX / Warp / Taichi), with the tie
broken by team size — "Rust if one person; GPU if someone already knows the
stack."

## Decision

Rust for the simulator, Python for aggregation and figures.

The two are separated by a JSONL file, not a binding. The simulator writes one
record per trial; the harness reads records. Neither knows anything about the
other beyond that schema.

## Consequences

* Runs parallelise over trials with rayon, which is the axis that matters —
  trials are independent and there are 10⁵ of them.
* No GPU dependency, so the same code runs on a laptop, in CI, and on a cluster.
* Config is TOML on the way in and JSON inside the crate, so a sweep override, a
  config file and a Python-generated config are the same thing.
* The cost: two languages, and a serialisation boundary. Accepted, because the
  boundary is also what lets figures be regenerated without re-running anything.
* If the GPU route is revisited later, the JSONL schema is the contract to keep.

## Measured

Release build, 4 cores: ~0.25 s per trial at n = 20, τ = 600 s, dt = 0.1 s.
The n² sensor loop dominates. See `docs/validation.md` for the throughput
measurement and what it implies for the 10⁵–10⁶ run budget.
