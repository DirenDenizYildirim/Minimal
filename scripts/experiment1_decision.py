#!/usr/bin/env python3
"""Apply experiment 1's pre-registered decision rule to the held-out evaluation.

Pre-registered at `docs/preregistration/searched-s3-pursuer.md`, commit 577f15a.
This script implements that rule and nothing else — it does not choose thresholds,
it reads them from the constants below, which are transcribed from the
pre-registration and must not be edited to fit a result.

    python scripts/experiment1_decision.py           the tables and the verdict
    python scripts/experiment1_decision.py --json     the same, machine-readable

Runs no simulation. Every statistic comes from `swarm_harness.stats`: mean
per-robot survival with a **Wilson** interval on the pooled robot count (§12.1 D0
— the median of a per-run proportion at n = 20 can only land on a twentieth), and
medians with bootstrap CIs for dispersion.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
from swarm_harness.load import load_jsonl          # noqa: E402
from swarm_harness.stats import median_ci, wilson_ci  # noqa: E402

# ---- the pre-registered constants, transcribed from 577f15a --------------------
RULE_A_CELLS = 12          # of 25, disjointly better than B1 on survival
RULE_A_DISPERSION = 3.0    # dispersion among survivors must stay below this
RULE_B_ARC_CM = 50.0       # state-0 arc above this counts as "abandoned the task"
RULE_B_DISPERSION = 10.0   # and dispersion among survivors above this
SEED_SPREAD_RULE = 10.0    # per cent, §21's R0 agreement rule
H_RULE = 1.93              # the handling time the 25 cells are counted at
MIN_SURVIVORS = 3          # below this, "dispersion among survivors" is degenerate

BASELINE = "B1-ternary"
SEARCH_A = [f"S3-survival-s{i}" for i in (1, 2, 3)]
SEARCH_B = [f"S3-survival_task-s{i}" for i in (1, 2, 3)]
VMAX, AXLE = 0.128, 0.051


def state0_arc_cm(constants) -> float:
    """The radius of the circle a robot drives when it sees nothing, in cm.

    Straight-line motion has no finite radius; the rule is "> 50 cm", so an
    infinite arc satisfies it and is reported as such rather than as an error.
    """
    left, right = constants[0] * VMAX, constants[1] * VMAX
    if left == right:
        return float("inf")
    return abs(0.5 * (left + right) * AXLE / (right - left)) * 100.0


def survival(rows):
    """Mean per-robot survival with a Wilson interval on the pooled robot count."""
    flags = []
    for x in rows:
        n, s = int(x["n"]), int(x["survivors"])
        flags.extend([1.0] * s + [0.0] * (n - s))
    return wilson_ci(flags)


def dispersion_among_survivors(rows):
    keep = [x["final_dispersion"] for x in rows if x["survivors"] >= MIN_SURVIVORS]
    if len(keep) < MIN_SURVIVORS:
        return (float("nan"),) * 3 + (len(keep),)
    return median_ci(keep) + (len(keep),)


def main() -> int:
    r = load_jsonl(REPO / "results" / "pursuer_searched_s3.jsonl")
    searched = {json.loads(p.read_text())["seed"]: p for p in
                sorted((REPO / "results").glob("search_s3_pursuer_*.json"))}
    constants = {}
    reported = {}
    for p in sorted((REPO / "results").glob("search_s3_pursuer_*.json")):
        s = json.loads(p.read_text())
        obj = "survival_task" if "survival_task" in p.name else "survival"
        constants[f"S3-{obj}-s{s['seed']}"] = s["best_constants"]
        reported[f"S3-{obj}-s{s['seed']}"] = s["best_training_objective"]

    ranges = r.unique("pursuer.range")
    kappas = r.unique("pursuer.confusion")
    out: dict = {"rule_source": "docs/preregistration/searched-s3-pursuer.md @ 577f15a"}

    # ---- rule (a): does a Search-B row beat B1 in >= 12 of the 25 cells? -------
    base_cells = {}
    for rp in ranges:
        for k in kappas:
            base_cells[(rp, k)] = survival(
                r.filter(row=BASELINE, **{"pursuer.range": rp, "pursuer.confusion": k,
                                          "pursuer.handling_time": H_RULE}).rows)
    print(f"RULE (a) — a Search-B row beats {BASELINE} on mean per-robot survival with")
    print(f"disjoint Wilson intervals in >= {RULE_A_CELLS} of 25 cells at h = {H_RULE} s,")
    print(f"while dispersion among survivors stays < {RULE_A_DISPERSION}.\n")
    print(f"{'row':24s} {'better':>7} {'worse':>6} {'overlap':>8}  {'dispersion among survivors':>28}  verdict")
    a_fired = []
    for row in SEARCH_B + SEARCH_A:
        better = worse = same = 0
        for rp in ranges:
            for k in kappas:
                cell = r.filter(row=row, **{"pursuer.range": rp, "pursuer.confusion": k,
                                            "pursuer.handling_time": H_RULE}).rows
                p, lo, hi = survival(cell)
                _, blo, bhi = base_cells[(rp, k)]
                if lo > bhi:
                    better += 1
                elif hi < blo:
                    worse += 1
                else:
                    same += 1
        d = dispersion_among_survivors(
            r.filter(row=row, **{"pursuer.handling_time": H_RULE}).rows)
        ok = (better >= RULE_A_CELLS and row in SEARCH_B
              and np.isfinite(d[0]) and d[0] < RULE_A_DISPERSION)
        if ok:
            a_fired.append(row)
        verdict = "FIRES (a)" if ok else ("cells ok, dispersion fails"
                                          if better >= RULE_A_CELLS else "—")
        dtxt = "n/a" if not np.isfinite(d[0]) else f"{d[0]:.2f} [{d[1]:.2f}, {d[2]:.2f}] n={d[3]}"
        print(f"{row:24s} {better:7d} {worse:6d} {same:8d}  {dtxt:>28}  {verdict}")
        out.setdefault("rule_a", {})[row] = dict(better=better, worse=worse, overlap=same,
                                                 dispersion=None if not np.isfinite(d[0]) else d[0])

    # ---- rule (b): did the survival-only search abandon the task? -------------
    print(f"\nRULE (b) — the Search-A rows converge toward D-dispersive: state-0 arc")
    print(f"> {RULE_B_ARC_CM:g} cm AND dispersion among survivors > {RULE_B_DISPERSION:g}.\n")
    print(f"{'row':24s} {'state-0 arc':>13}  {'dispersion among survivors':>28}  verdict")
    b_fired = []
    for row in SEARCH_A + SEARCH_B + [BASELINE, "D-dispersive"]:
        arc = state0_arc_cm(constants[row]) if row in constants else state0_arc_cm(
            {"B1-ternary": [-0.7, -1.0], "D-dispersive": [-0.95, -1.0]}[row])
        d = dispersion_among_survivors(
            r.filter(row=row, **{"pursuer.handling_time": H_RULE}).rows)
        fires = (row in SEARCH_A and arc > RULE_B_ARC_CM
                 and np.isfinite(d[0]) and d[0] > RULE_B_DISPERSION)
        if fires:
            b_fired.append(row)
        dtxt = "n/a" if not np.isfinite(d[0]) else f"{d[0]:.2f} [{d[1]:.2f}, {d[2]:.2f}]"
        atxt = "infinite (straight)" if not np.isfinite(arc) else f"{arc:.1f} cm"
        print(f"{row:24s} {atxt:>13}  {dtxt:>28}  {'FIRES (b)' if fires else '—'}")
        out.setdefault("rule_b", {})[row] = dict(arc_cm=None if not np.isfinite(arc) else arc,
                                                 dispersion=None if not np.isfinite(d[0]) else d[0])

    # ---- seed spread against §21's 10% rule ----------------------------------
    print(f"\nSEED SPREAD — state-0 R0 across the three optimiser seeds, against §21's")
    print(f"{SEED_SPREAD_RULE:g}% agreement rule.\n")
    for label, group in (("survival", SEARCH_A), ("survival_task", SEARCH_B)):
        arcs = [state0_arc_cm(constants[row]) for row in group]
        if all(np.isfinite(a) for a in arcs):
            spread = 100 * (max(arcs) - min(arcs)) / float(np.mean(arcs))
            print(f"  {label:14s} {' / '.join(f'{a:.2f}' for a in arcs)} cm"
                  f"   spread {spread:.1f}% — {'within' if spread <= SEED_SPREAD_RULE else 'OUTSIDE'} the rule")
            out.setdefault("seed_spread", {})[label] = spread
        else:
            print(f"  {label:14s} at least one seed drives straight; R0 spread is undefined,"
                  f" which is itself outside any agreement rule")
            out.setdefault("seed_spread", {})[label] = None

    # ---- the winner's curse --------------------------------------------------
    print("\nREPORTED vs RE-SCORED training objective (the winner's-curse gap).")
    rescore = REPO / "results" / "pursuer_searched_s3_rescore.jsonl"
    if rescore.exists():
        rs = load_jsonl(rescore)
        conds = sorted({(x["pursuer.range"], x["pursuer.confusion"]) for x in rs.rows})
        for row in SEARCH_A + SEARCH_B:
            per = []
            for rp, k in conds:
                cell = rs.filter(row=row, **{"pursuer.range": rp, "pursuer.confusion": k}).rows
                s = survival(cell)[0]
                if "survival_task" in row:
                    keep = [x["final_dispersion"] for x in cell if x["survivors"] >= MIN_SURVIVORS]
                    s = 0.0 if not keep or s <= 0 else float(np.sqrt(s / np.median(keep)))
                per.append(s)
            honest = 0.0 if any(v <= 0 for v in per) else float(np.exp(np.mean(np.log(per))))
            gap = reported[row] - honest
            print(f"  {row:24s} reported {reported[row]:.4f}   honest {honest:.4f}   gap {gap:+.4f}")
            out.setdefault("winners_curse", {})[row] = dict(reported=reported[row],
                                                            honest=honest, gap=gap)
    else:
        print(f"  {rescore.name} not present — run the re-score sweep first.")

    # ---- verdict -------------------------------------------------------------
    print("\nVERDICT under the pre-registered rule:")
    if a_fired:
        print(f"  (a) FIRES for {', '.join(a_fired)} — G4 is upgraded to a measured")
        print("      upper bound, stated with †.")
    if b_fired:
        print(f"  (b) FIRES for {', '.join(b_fired)} — a survival-only search abandons")
        print("      the task; report as a finding supporting the two-axis (B5) framing.")
    if not a_fired:
        print("  (c) G4 stays SUGGESTED with its existing hedge. The searched rows are")
        print("      further evidence that the hand-designed rows are not far from what a")
        print("      class search of this budget finds — a weaker claim than (a), and it")
        print("      must not be written as if it were (a).")
    out["verdict"] = dict(rule_a=a_fired, rule_b=b_fired, rule_c=not a_fired)

    if "--json" in sys.argv:
        print("\n" + json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
