# 0002 — Sign convention for the terrain gravity term

**Status:** accepted, 2026-09-04.

## Context

The build doc (§3, Idea A) gives the corrected per-wheel terrain model as

```
v_w = v_cmd,w · m_w(x, y)  −  g_eff · sin(α) · (ĥ · ŝ)
```

and describes `ŝ` as "the downhill direction". Taken literally, a robot pointed
downhill has `ĥ · ŝ = +1` and therefore *loses* speed, which is backwards: on a
tilted board, gravity speeds up a robot heading down the fall line.

## Decision

Keep the equation exactly as written, including the minus sign, and define
`slope_dir` as the **uphill** direction.

Then `ĥ · ŝ = +1` pointing uphill (speed is reduced) and `−1` pointing downhill
(speed is gained), which is what the hardware does.

## Consequences

* The implementation matches the build doc term for term; only the reading of
  `ŝ` changes, and it is documented at the definition of `TerrainConfig::slope_dir`.
* `terrain::tests::gravity_term_is_heading_dependent_and_signed_downhill_positive`
  pins the sign, so this cannot drift.
* Anyone comparing the code against the build doc should read this file first.
  If the doc is revised to say "uphill", this ADR becomes a no-op rather than a
  contradiction.

## Note on `g_eff`

`g_eff` carries velocity units (m/s) in this formulation, not acceleration: it
is a phenomenological gain to be calibrated against the tiltable board, not `9.81`.
The config field is named `slope_gain` to avoid implying otherwise.
