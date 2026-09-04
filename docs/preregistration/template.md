# Pre-registration — <experiment name>

Fill this in and commit it **before** running the sweep. The commit hash of this
file is what makes the threshold pre-registered rather than chosen after seeing
the surface.

## Question

One sentence. Which capability rows, which hostility dial, what is being decided.

## Task and threshold

* Behaviour: <aggregation | ...>
* Primary metric: <e.g. `final_dispersion`, median over runs in a cell>
* Threshold `T`: <value>, direction <lower is better | higher is better>
* Secondary metrics, reported but not thresholded: <...>
* Cluster link distance, if any cluster metric is reported: <k> body radii

## Capability rows

| Row | S | M | A | K | Provenance | Free constants | Enumerable at Gauci's resolution? |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

Rows that are not enumerated yield **upper bounds** on `c*(θ)`. State that here
and in the abstract.

## Environment grid

| Dial | Values | Notes |
|---|---|---|
|  |  |  |

Fixed parameters that a reader needs in order to interpret the grid (correlation
length `λ` and its ratio to `R0`, `g_eff`, swarm size `n`, τ, dt):

## Design

* Runs per cell: <≥ 100 Tier 1 / ≥ 30 Tier 2>
* Seed: <value>. Runs are indexed, so any cell is reproducible in isolation.
* Statistics: medians with 95% percentile-bootstrap CIs; Friedman + post-hoc
  across rows.
* Search budget per optimiser-found cell: <...>

## Predictions

State them before looking. A hypothesis that could not have failed is not a
hypothesis.

* H1:
* H2:

## Deviations

Anything that changed after registration, and why. Append; do not edit above.
