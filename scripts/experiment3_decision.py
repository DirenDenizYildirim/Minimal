#!/usr/bin/env python3
"""Apply experiment 3's pre-registered decision rule: does A3 hold at a second λ?

Pre-registered at `docs/preregistration/lambda-tuning-control.md`, commit d6c40c8.
This script implements that rule and nothing else. The rule, verbatim:

> **Per λ, reported separately. The three correlation lengths are not pooled.**
>
> * **A3 holds at that λ** if the **paired terrain-tuning interval includes zero**
>   there.
> * **A3 fails at that λ** if the interval **excludes** zero. Direction matters and
>   is reported either way: an interval excluding zero *above* means terrain-tuning
>   buys something real at that λ, which would narrow A3 rather than overturn it; an
>   interval excluding zero *below* means the terrain-trained row is worse than the
>   flat-trained one under terrain, which would be a stronger result than A3 and must
>   not be reported as a mere failure.
> * **The matched-controller cost is reported as a range across the three λ**
>   (0.05, 0.10, 0.20 m), replacing the single-λ figure A2 currently quotes.
> * The crossing is reported if present at any λ, with its interval, and is **not**
>   claimed as a result unless it is disjoint from zero at more than one λ.

    python scripts/experiment3_decision.py          the tables and the verdicts
    python scripts/experiment3_decision.py --json   the same, machine-readable

Runs no simulation. Two quantities, and they are not the same thing:

**The terrain-tuning TERM** is the paired per-run difference
`D(S2-flat) − D(S2-rough)` at θ_m = 0.9 — positive means the terrain-trained row
is the better one — with a percentile-bootstrap interval. This is what the rule
turns on, and it is a paired quantity because both rows share a seed base, so
run *i* is the same placement and the same field in both.

**The terrain-tuning SHARE** is a decomposition of *levels*:
`median(gauci) − median(flat)` is the objective-tuning part and
`median(flat) − median(rough)` the terrain part, and they add to the whole gap
because levels are additive and per-run ratios are not. §14 and the
pre-registration both spell out why this one is deliberately not paired. It is
reported, not thresholded.

**The matched-controller COST** is `hold ratio − 1` for the two tuned rows: what
θ_m = 0.9 costs a controller that was tuned for this objective, against the same
controller's own flat ground. A2 currently quotes 10–20% from one λ; the rule
replaces that with the range over three.

One definitional wrinkle that must not be read as a λ effect. A2's "10–20%" comes
from §13's **retired** ratio-of-medians hold ratios (1.195 and 1.104 → 19.5% and
10.4%). This script uses §12.1 D1's **paired** ratios throughout, which at the
very same 100 runs give 1.2004 and 1.0988 → **20.0% and 9.9%**. So the λ = 0.10 m
column here will not match A2's digits exactly, and the difference is the change
of statistic §12.1 D1 already settled, not a difference between correlation
lengths. §14 quotes the paired form and this agrees with it to four decimals.

A LIMITATION THIS SCRIPT CANNOT REMOVE, and which every number below inherits.
Both tuned rows were trained at λ = 0.10 m. At λ = 0.05 and 0.20 m this measures
the *transfer* of a λ = 0.10-tuned controller, not the decomposition a
λ-matched controller would show. A terrain term that shrinks at a new λ is
consistent with "the term is small everywhere" and with "the term is real but
does not transfer", and this design cannot separate them.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "harness" / "src"))
from swarm_harness.load import Records, load_jsonl   # noqa: E402
from swarm_harness.stats import median_ci            # noqa: E402

ROWS = ("S2-gauci", "S2-flat", "S2-rough")
THETAS = (0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9)
ROUGH, FLAT = 0.9, 0.0
CROSSING_THETA = 0.6

# λ = 0.10 m is the EXISTING record and is not re-run: it lives in
# terrain_tuning_control.jsonl, where λ is a row override rather than an axis, so
# it carries no correlation_length coordinate and is selected by taking the file
# whole. The two new λ share one file and are selected by the axis coordinate.
SOURCES = {
    0.05: ("terrain_tuning_control_lambda", {"terrain.correlation_length": 0.05}),
    0.10: ("terrain_tuning_control", {}),
    0.20: ("terrain_tuning_control_lambda", {"terrain.correlation_length": 0.20}),
}

_CACHE: dict[str, Records] = {}


def records(name: str) -> Records:
    if name not in _CACHE:
        _CACHE[name] = load_jsonl(REPO / "results" / f"{name}.jsonl")
    return _CACHE[name]


def cells(lam: float, row: str, theta: float) -> dict[int, float]:
    """Run index -> final dispersion, for one (λ, row, θ_m) cell."""
    name, sel = SOURCES[lam]
    got = records(name).filter(row=row, **{"terrain.friction_amplitude": theta}, **sel)
    return {x["run_index"]: x["final_dispersion"] for x in got.rows}


def paired(a: dict[int, float], b: dict[int, float]):
    """median_ci of a − b over the run indices both share."""
    keys = sorted(set(a) & set(b))
    return median_ci([a[k] - b[k] for k in keys]) + (len(keys),)


def hold_ratio(lam: float, row: str):
    """Dispersion at θ_m = 0.9 over the SAME RUN's flat ground, paired by index."""
    rough, flat = cells(lam, row, ROUGH), cells(lam, row, FLAT)
    keys = sorted(set(rough) & set(flat))
    return median_ci([rough[k] / flat[k] for k in keys if flat[k]]) + (len(keys),)


def decomposition(lam: float):
    """Objective-tuning and terrain-tuning shares of the anchor-to-rough gap.

    Levels, on the run indices all three rows share — the same construction as
    `recompute_paired_and_survival.py::decomposition`, which this deliberately
    mirrors rather than replaces so the λ = 0.10 m column reproduces §14 exactly.
    """
    d = {r: cells(lam, r, ROUGH) for r in ROWS}
    keys = sorted(set(d["S2-gauci"]) & set(d["S2-flat"]) & set(d["S2-rough"]))
    lev = {r: float(np.median([d[r][k] for k in keys])) for r in ROWS}
    gap = lev["S2-gauci"] - lev["S2-rough"]
    return dict(
        levels={r: round(v, 4) for r, v in lev.items()},
        gap=round(gap, 4),
        objective_pct=round(100 * (lev["S2-gauci"] - lev["S2-flat"]) / gap, 1),
        terrain_pct=round(100 * (lev["S2-flat"] - lev["S2-rough"]) / gap, 1),
        runs=len(keys),
    )


def verdict_for(lo: float, hi: float) -> tuple[str, str]:
    if lo > 0:
        return ("A3 FAILS at this λ — excludes zero ABOVE", "narrows A3: terrain-tuning "
                "buys something real here. Not an overturn.")
    if hi < 0:
        return ("A3 FAILS at this λ — excludes zero BELOW", "STRONGER than A3: the "
                "terrain-trained row is worse than the flat-trained one under terrain. "
                "Must not be filed as a mere failure.")
    return ("A3 HOLDS at this λ", "the paired terrain-tuning interval includes zero")


def evaluate_lambda(lam: float, out: dict) -> dict:
    name, sel = SOURCES[lam]
    print(f"\n{'='*78}\nλ = {lam:.2f} m   (results/{name}.jsonl"
          + (f", {list(sel)[0]} = {list(sel.values())[0]}" if sel else ", whole file") + ")")
    print("=" * 78)

    print("\n  hold ratio at θ_m = 0.9 (paired per run, 95% CI)   "
          "— matched-controller cost is (ratio − 1)")
    holds = {}
    for row in ROWS:
        m, lo, hi, n = hold_ratio(lam, row)
        holds[row] = dict(value=round(m, 4), lo=round(lo, 4), hi=round(hi, 4),
                          cost_pct=round(100 * (m - 1), 1), n=n)
        tag = "  (anchor, tuned for neither)" if row == "S2-gauci" else "  †"
        print(f"    {row:10s} {m:7.4f} [{lo:.4f}, {hi:.4f}]   "
              f"cost {100*(m-1):+6.1f} %{tag}")

    print("\n  paired terrain term  D(S2-flat) − D(S2-rough)  at every θ_m"
          "   (+ = the terrain-trained row is better)")
    table = {}
    for theta in THETAS:
        m, lo, hi, n = paired(cells(lam, "S2-flat", theta), cells(lam, "S2-rough", theta))
        sign = ("rough better" if lo > 0 else "flat better" if hi < 0 else "no difference")
        table[f"{theta:g}"] = dict(value=round(m, 4), lo=round(lo, 4), hi=round(hi, 4),
                                   n=n, verdict=sign)
        star = "  <- the rule is evaluated here" if theta == ROUGH else (
               "  <- the crossing cell" if theta == CROSSING_THETA else "")
        print(f"    θ_m = {theta:<5g} {m:+8.4f} [{lo:+.4f}, {hi:+.4f}]  {sign:14s}{star}")

    dec = decomposition(lam)
    print(f"\n  level decomposition of the S2-gauci → S2-rough gap at θ_m = 0.9 "
          f"(gap {dec['gap']:.4f})")
    print(f"    objective-tuning {dec['objective_pct']:5.1f} %      "
          f"terrain-tuning {dec['terrain_pct']:5.1f} %      "
          f"levels {dec['levels']['S2-gauci']:.4f} / {dec['levels']['S2-flat']:.4f}"
          f" / {dec['levels']['S2-rough']:.4f}")
    print("    (levels, not paired ratios — see the docstring; reported, not thresholded)")

    rule = table[f"{ROUGH:g}"]
    verdict, gloss = verdict_for(rule["lo"], rule["hi"])
    print(f"\n  >>> {verdict}")
    print(f"      {gloss}")
    print(f"      terrain term at θ_m = 0.9: {rule['value']:+.4f} "
          f"[{rule['lo']:+.4f}, {rule['hi']:+.4f}] over {rule['n']} paired runs")

    entry = dict(source=f"results/{name}.jsonl", selector=sel, hold_ratios=holds,
                 terrain_term=table, decomposition=dec, verdict=verdict, gloss=gloss)
    out["per_lambda"][f"{lam:g}"] = entry
    return entry


def pairing_check(out: dict) -> bool:
    """Is "the same experiment at a different λ" true, or only approximate?

    The design rests on run *i* being the same initial placement at every λ, so
    that the new cells pair by run index against the existing ones. That follows
    from the same base seed, the same n and the same coverage — but it is cheap
    to check rather than assert, and the check is sharp: the initial dispersion
    is fixed before the first step and cannot depend on the terrain field, so if
    the placements match it must agree to the last bit at every λ.
    """
    print(f"{'='*78}\nPAIRING CHECK — is run i the same placement at every λ?\n{'='*78}")
    ok = True
    for row in ROWS:
        ref = {x["run_index"]: (x["seed"], x["initial_dispersion"])
               for x in records("terrain_tuning_control")
               .filter(row=row, **{"terrain.friction_amplitude": ROUGH}).rows}
        for lam in (0.05, 0.20):
            got = {x["run_index"]: (x["seed"], x["initial_dispersion"])
                   for x in records("terrain_tuning_control_lambda")
                   .filter(row=row, **{"terrain.friction_amplitude": ROUGH},
                           **{"terrain.correlation_length": lam}).rows}
            keys = sorted(set(ref) & set(got))
            bad = [k for k in keys if ref[k] != got[k]]
            ok &= not bad and len(keys) == len(ref)
            print(f"  {row:10s} λ = {lam:.2f} m vs 0.10 m: {len(keys)} shared run indices, "
                  f"{len(bad)} disagree on (seed, initial dispersion)")
    print(f"\n  >>> {'runs pair exactly across λ' if ok else 'PAIRING IS BROKEN — the rule below is not the registered one'}")
    out["pairing_exact"] = bool(ok)
    return ok


def main() -> int:
    out: dict = {"rule_source": "docs/preregistration/lambda-tuning-control.md @ d6c40c8",
                 "per_lambda": {}}

    missing = [f"results/{n}.jsonl" for n in {s[0] for s in SOURCES.values()}
               if not (REPO / "results" / f"{n}.jsonl").exists()]
    if missing:
        print("missing: " + ", ".join(missing), file=sys.stderr)
        return 1

    pairing_check(out)

    for lam in sorted(SOURCES):
        evaluate_lambda(lam, out)

    print(f"\n{'='*78}\nACROSS THE THREE λ — the rule's two cross-λ clauses\n{'='*78}")

    # Clause: the matched-controller cost becomes a RANGE over λ.
    costs = {row: [out["per_lambda"][f"{l:g}"]["hold_ratios"][row]["cost_pct"]
                   for l in sorted(SOURCES)] for row in ("S2-flat", "S2-rough")}
    lo_c = min(min(v) for v in costs.values())
    hi_c = max(max(v) for v in costs.values())
    print("\n  matched-controller cost at θ_m = 0.9, per λ (0.05 / 0.10 / 0.20 m):")
    for row, vs in costs.items():
        print(f"    {row:10s} " + " / ".join(f"{v:+.1f} %" for v in vs))
    print(f"\n    range across the three λ and both tuned rows: "
          f"{lo_c:+.1f} % to {hi_c:+.1f} %")
    print(f"    A2 currently states 10-20 % from λ = 0.10 m alone; the rule replaces")
    print(f"    that with this range, and says it is a range over λ.")
    out["matched_controller_cost"] = dict(
        per_lambda={row: dict(zip([f"{l:g}" for l in sorted(SOURCES)], vs))
                    for row, vs in costs.items()},
        range_pct=[round(lo_c, 1), round(hi_c, 1)],
        supersedes="A2's single-λ 10-20 %")

    # Clause: the crossing is claimed only if disjoint from zero at MORE THAN ONE λ.
    cross = {f"{l:g}": out["per_lambda"][f"{l:g}"]["terrain_term"][f"{CROSSING_THETA:g}"]
             for l in sorted(SOURCES)}
    disjoint = [k for k, v in cross.items() if v["lo"] > 0 or v["hi"] < 0]
    print(f"\n  the θ_m = {CROSSING_THETA:g} crossing, per λ:")
    for k, v in cross.items():
        mark = "  DISJOINT from zero" if k in disjoint else "  includes zero"
        print(f"    λ = {k:<5s} {v['value']:+.4f} [{v['lo']:+.4f}, {v['hi']:+.4f}]{mark}")
    claimed = len(disjoint) > 1
    print(f"\n    disjoint at {len(disjoint)} of {len(cross)} λ -> the crossing is "
          + ("CLAIMED as a result" if claimed else "REPORTED but NOT CLAIMED"))
    out["crossing"] = dict(theta=CROSSING_THETA, per_lambda=cross,
                           disjoint_at=disjoint, claimed=bool(claimed))

    verdicts = {k: v["verdict"] for k, v in out["per_lambda"].items()}
    print(f"\n{'='*78}\nVERDICTS (never pooled)\n{'='*78}")
    for k, v in verdicts.items():
        print(f"  λ = {k:<5s} {v}")

    if "--json" in sys.argv:
        print("\n" + json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
