# 0003 — Dispersion is the primary metric; cluster counts are secondary

**Status:** accepted, 2026-09-04.

## Context

The build doc (Idea A) lists three metrics: dispersion at τ (Gauci's),
single-cluster fraction, and time to single cluster — all in the centroid frame.

Running the baseline surfaced a problem with the cluster-based ones. An
aggregated swarm keeps one robot hovering near the link threshold, so the boolean
"is the swarm exactly one cluster?" flips between consecutive samples. Every one
of 30 baseline runs hit one cluster and then split again at least once.

The link distance has no canonical value, and the cluster metrics depend on it
strongly while dispersion does not at all
(`configs/sweeps/link_distance_sensitivity.toml`, 30 runs/cell):

| link distance | single cluster at τ | share of time single | final dispersion |
|---|---|---|---|
| 2.2 R | 0.73 | 0.43 | 1.401 |
| 3.0 R | 0.90 | 0.77 | 1.401 |
| 4.0 R | 1.00 | 0.92 | 1.401 |
| 6.0 R | 1.00 | 0.98 | 1.401 |

## Decision

1. **Dispersion at τ is the primary metric** and is what the pre-registered
   threshold `T` is set on. It has no free parameter.
2. Cluster-count metrics are reported as secondary, always with the link
   distance used. The default is 3.0 R (a gap of one body radius).
3. `single_cluster` at τ is kept for comparability but is not a headline number.
   Prefer `fraction_time_single_cluster`, which averages over the flicker, and
   `final_largest_cluster_fraction`, which degrades gracefully (0.95 with one
   straggler rather than flipping to false).
4. `time_to_first_single_cluster` is named for what it measures. It fires on the
   first transient chain and is not "time to aggregate".

## Consequences

* Any cluster-count claim in a paper must state the link distance, and the
  sensitivity sweep above must be re-run if the arena or `n` changes.
* `world::tests::dispersion_ignores_the_link_distance_but_cluster_counts_do_not`
  is the regression guard.

## Open

`metrics::dispersion` uses the Graham & Sloane normalised second moment,
`u = 2 Σ|pᵢ − p̄|² / (n² R²)`, derived so that a perfectly packed cluster scores
~1 (the baseline lands at 1.40). **The exact constant must be checked against
Gauci et al. before any absolute dispersion value is quoted** — see
`docs/validation.md`. Ordering between runs and scaling in `n` are unaffected by
the constant.
