#!/usr/bin/env python3
"""Apply experiment 2's pre-registered decision rule: does A1 hold at n ∈ {10, 50}?

Pre-registered at `docs/preregistration/capability-flatness-n.md`, commit 0dd7ae1.
This script implements that rule and nothing else. The rule, verbatim:

> **A1 holds at that n** if no S = 4 row's hold ratio at θ_m = 0.9 is below the
> best S = 2 row's with disjoint intervals. "Best S = 2 row" is the best-of-three
> class-flat baseline together with S2-searched, taken per cell.
> **A1 fails at that n** if either S = 4 row is disjointly below every S = 2 row.
> **Neither** is reported as such, with the rows named.

    python scripts/experiment2_decision.py          the tables and the verdict
    python scripts/experiment2_decision.py --json   the same, machine-readable

Runs no simulation. The hold ratio is the **paired per-run ratio** — dispersion
at θ_m = 0.9 over the same run's flat-ground dispersion — which is §12.1 D1's
single definition and the one the paper is settling on. Reach is a proportion and
gets a Wilson interval, never a median.

**Lower is better for a hold ratio**, so "below" in the rule means *better*. The
rule asks whether an S = 4 row is disjointly BETTER than every S = 2 row; A1
holding means no S = 4 row manages that.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
from swarm_harness.load import Records, load_jsonl      # noqa: E402
from swarm_harness.stats import median_ci, wilson_ci    # noqa: E402

S2_ROWS = ["S2-class-flat-s1", "S2-class-flat-s2", "S2-class-flat-s3", "S2-searched"]
S4_ROWS = ["S4-terrain", "S4-warm"]
REFERENCE = "S2-gauci"
ROUGH, FLAT = 0.9, 0.0
REACH_FLOOR = 0.8          # the pre-registered τ contingency trigger


def hold_ratio(records: Records, row: str, n: int, duration: float | None = None):
    """Dispersion at θ_m = 0.9 over the SAME RUN's flat ground, paired by index."""
    kw = {"row": row, "swarm.n": n}
    if duration is not None:
        kw["sim.duration"] = duration
    flat = {x["run_index"]: x["final_dispersion"]
            for x in records.filter(**kw, **{"terrain.friction_amplitude": FLAT}).rows}
    rough = records.filter(**kw, **{"terrain.friction_amplitude": ROUGH}).rows
    xs = [x["final_dispersion"] / flat[x["run_index"]]
          for x in rough if x["run_index"] in flat and flat[x["run_index"]]]
    return median_ci(xs)


def reach(records: Records, row: str, n: int, amp: float, duration=None):
    kw = {"row": row, "swarm.n": n, "terrain.friction_amplitude": amp}
    if duration is not None:
        kw["sim.duration"] = duration
    c = records.filter(**kw)
    return wilson_ci([1.0 if x else 0.0 for x in c.column("ever_single_cluster")])


def evaluate_n(records: Records, n: int, label: str, duration=None, out=None):
    print(f"\n{'='*74}\nn = {n}   ({label})\n{'='*74}")
    stats = {row: hold_ratio(records, row, n, duration)
             for row in [REFERENCE] + S2_ROWS + S4_ROWS}
    print(f"{'row':22s} {'hold ratio at θ_m = 0.9 (paired, 95% CI)':>42s}   {'reach θ_m=0.9':>16s}")
    for row in [REFERENCE] + S2_ROWS + S4_ROWS:
        m, lo, hi = stats[row]
        p, plo, phi = reach(records, row, n, ROUGH, duration)
        mark = "  (S = 4)" if row in S4_ROWS else ("  ref" if row == REFERENCE else "")
        print(f"{row:22s} {m:11.4f} [{lo:.4f}, {hi:.4f}]{'':>13} {p:.2f} [{plo:.2f}, {phi:.2f}]{mark}")

    # "best S = 2 row" = the smallest hold ratio among the four S = 2 rows.
    best_s2 = min(S2_ROWS, key=lambda r: stats[r][0])
    b = stats[best_s2]
    print(f"\nbest S = 2 row: {best_s2}  {b[0]:.4f} [{b[1]:.4f}, {b[2]:.4f}]")

    verdicts = {}
    for s4 in S4_ROWS:
        a = stats[s4]
        better_than_best = a[2] < b[1]
        better_than_all = all(a[2] < stats[r][1] for r in S2_ROWS)
        worse_than_best = a[1] > b[2]
        verdicts[s4] = dict(hold=a[0], lo=a[1], hi=a[2],
                            disjointly_better_than_best=bool(better_than_best),
                            disjointly_better_than_every_s2=bool(better_than_all),
                            disjointly_worse_than_best=bool(worse_than_best))
        state = ("disjointly BETTER than every S = 2 row" if better_than_all else
                 "disjointly better than the best S = 2 row only" if better_than_best else
                 "disjointly WORSE than the best S = 2 row" if worse_than_best else
                 "overlapping the best S = 2 row")
        print(f"  {s4:16s} {a[0]:.4f} [{a[1]:.4f}, {a[2]:.4f}]  — {state}")

    any_better_all = any(v["disjointly_better_than_every_s2"] for v in verdicts.values())
    any_better_best = any(v["disjointly_better_than_best"] for v in verdicts.values())
    if any_better_all:
        verdict = "A1 FAILS at this n"
    elif not any_better_best:
        verdict = "A1 HOLDS at this n"
    else:
        named = [k for k, v in verdicts.items() if v["disjointly_better_than_best"]]
        verdict = f"NEITHER at this n — {', '.join(named)} beats the best S = 2 row but not every one"
    print(f"\n  >>> {verdict}")
    if out is not None:
        out[f"n={n}" + (f",tau={duration:g}" if duration else "")] = dict(
            label=label, best_s2=best_s2,
            hold_ratios={k: list(v) for k, v in stats.items()},
            s4=verdicts, verdict=verdict)
    return verdict


def main() -> int:
    out: dict = {"rule_source": "docs/preregistration/capability-flatness-n.md @ 0dd7ae1"}
    base = load_jsonl(REPO / "results" / "terrain_capability_n.jsonl")

    print("PRE-REGISTERED τ CONTINGENCY: any row below "
          f"{REACH_FLOOR:g} reach at n = 10, θ_m = 0.9, τ = 600 s re-runs the block at 3600 s.")
    low = {row: reach(base, row, 10, ROUGH)[0] for row in [REFERENCE] + S2_ROWS + S4_ROWS}
    fired = [r for r, p in low.items() if p < REACH_FLOOR]
    print(f"  rows below {REACH_FLOOR:g}: " + (", ".join(f"{r} {low[r]:.2f}" for r in fired) or "none")
          + f"  ->  contingency {'FIRES' if fired else 'does not fire'}")
    out["tau_contingency"] = dict(fired=bool(fired), rows={r: low[r] for r in fired})

    # The two swarm sizes are reported SEPARATELY and never pooled: "A1 holds at
    # n = 10 and fails at n = 50" is a publishable answer that pooling would hide.
    evaluate_n(base, 50, "τ = 600 s", out=out)
    evaluate_n(base, 10, "τ = 600 s — TRUNCATED, see the contingency", out=out)

    tau_path = REPO / "results" / "terrain_capability_n_tau.jsonl"
    if fired:
        if tau_path.exists():
            evaluate_n(load_jsonl(tau_path), 10,
                       "τ = 3600 s — THE RULE IS EVALUATED HERE", duration=3600.0, out=out)
        else:
            print(f"\n{tau_path.name} not present — the contingency fired and the re-run "
                  "has not been done, so n = 10 has no verdict yet.")
    if "--json" in sys.argv:
        print("\n" + json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
