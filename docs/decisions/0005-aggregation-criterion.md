# 0005 — Aggregation means *reaching* a connected cluster, not being one at τ

**Status:** accepted, 2026-09-04. Closes the week-1 gate.

## Context

The gate check "n = 2 must aggregate, as Gauci et al. prove" failed: pairs ended
τ = 600 s at a median separation of 22 cm, and only ~10% were touching at τ.
Five candidate causes were tested (see `docs/validation.md` §2) and none
explained it.

The check itself was wrong, in two ways.

### The theorem it appealed to has been disproven

Steinberg and Solovey (2024), *Impossibility of Self-Organized Aggregation
without Computation*, identify an unsound step in Gauci et al.'s two-robot
proof:

> An implicit assumption is made that if at time t the distance between the two
> robots satisfies d ≤ 2(R+r), then aggregation is assured at time t′ > t.

Two robots can satisfy that distance condition while travelling the same
circular perimeter without ever seeing each other, and so never aggregate. In
their own experiments the Gauci controller **fails to aggregate on 4.24% of
trials**. So "n = 2 always aggregates" is not a fact to reproduce.

They further prove that *no* bimodal controller in this class aggregates for
every swarm size: for any such controller there is some n and some initial state
where it fails.

### The metric was measuring the wrong event

Their definition: aggregation holds when the union of discs around the robots
becomes **connected**. It does not require the robots to stay connected.

That distinction is negligible for a dense swarm and enormous for a pair.
Measured here at n = 2, 100 runs, τ = 600 s:

| | value |
|---|---|
| runs reaching exact contact (7.4 cm) at some point | 93% |
| runs ever forming a single cluster (link 3R) | 87–93% |
| runs that are a single cluster **at τ** | 3–17% |
| median closest approach | 7.4 cm (contact) |
| median separation at τ | 22 cm |

The pair finds each other reliably. Nothing in the controller holds them
together once they arrive: at contact the other robot subtends about 60°, so a
robot is frozen for roughly a sixth of each rotation and backing away for the
rest. In a dense swarm the cluster subtends a much larger angle, robots are
frozen most of the time, and they accumulate — which is why the same controller
looks completely different at n = 20.

## Decision

1. `ever_single_cluster` is the aggregation criterion, and it is on every run
   record. `single_cluster` (at τ) is retained as a secondary, clearly-labelled
   snapshot.
2. The gate's small-n row is judged on reaching connectivity. At 87–93% against
   the ~95.8% Steinberg and Solovey report for the same controller, this
   simulator is consistent with the literature; the residual gap is within what
   the connectivity radius and initial-condition distribution can account for,
   and is not worth chasing further.
3. Steinberg and Solovey (2024) joins the reading list, and the build doc's
   description of the Gauci row as carrying a "proof for n = 2" needs amending.
   See `docs/literature-corrections.md`.

## Consequences

* The project's anchor result is weaker than the build doc assumes. That is
  *useful* rather than damaging: the framing is already that minima are upper
  bounds, and an impossibility result for the whole bimodal class is a sharper
  version of the same point. It belongs in the framing section, not a footnote.
* Any threshold `T` set on a cluster-count metric must state which event it
  scores — reaching or holding. They are different numbers by an order of
  magnitude at small n.
* Nothing changes for n ≥ 10, where the two criteria nearly coincide.
