# Statistics protocol

Pre-registered per paper, following the Birattari-lab / ANTS convention the
build doc adopts (§4).

## Run counts

* Tier 1 (this simulator): **≥ 100 runs per cell.** Sweep files state
  `runs_per_cell`; diagnostics that use fewer say so in a comment and must not
  be quoted as results.
* Tier 2 (ARGoS): **≥ 30 runs per cell.**

## Point estimates

**Medians with bootstrap confidence intervals**, not means. Performance
distributions within a cell are routinely bimodal — the swarm either aggregates
or it does not — and a mean lands between the two modes, where no run ever sits.
`swarm_harness.stats.summarise` reports median, 95% percentile-bootstrap CI, and
the mean and standard deviation alongside so the bimodality is visible.

The bootstrap is seeded, so a figure regenerates identically.

## Comparisons across capability rows

**Friedman test with post-hoc**, on cells matched across rows. This needs SciPy:

```bash
uv pip install --python .venv/bin/python 'swarm-harness[stats]'
```

`swarm_harness.stats.friedman_across_rows` raises a clear error rather than
falling back to a weaker test if SciPy is absent, because the venue expects this
specific one. **Status: the wrapper is written; no comparison has been run yet.**

## Thresholds

The task threshold `T` and the metric it is set on are **fixed per paper and
pre-registered** before the sweep runs — see `docs/preregistration/`. Reporting
several contours (T = 0.7, 0.8, 0.9) on one surface is not a substitute for
pre-registering one: the contours show how the answer depends on the bar; the
pre-registered `T` is the bar.

The primary metric is dispersion at τ. See `docs/decisions/0003-metrics.md` for
why the cluster-count metrics are secondary.

## Search budget

Every cell's record carries `provenance` and `minimum_is_tight`. For any
optimiser-found row, report the **search budget per cell**, and where feasible
run two independent optimisers and report their agreement. A row that is not
enumerated yields an upper bound on `c*(θ)`, and every abstract, figure and table
must say so.
