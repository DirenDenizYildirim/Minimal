#!/usr/bin/env python3
"""Join `verify_numbers.py` against §13, so "does it match" is checkable per row.

`scripts/verify_numbers.py` prints what it recomputed next to a `claimed` string
that was written into the script by hand. Some of those strings predate the
Phase A revision of §13 — the hold ratio moved from a ratio of medians to the
paired form, and the pursuer survival statistic from a median run-level fraction
to a mean per-robot proportion with a Wilson interval (`paper-source.md` §12.1
D0). Comparing the script against its own `claimed` column therefore answers a
question nobody asked. The number that has to reproduce is the one in §13.

This reads §13 from `docs/paper-source.json` (the machine-readable copy of the
same table), joins on the row id, and prints all three columns together with a
verdict. It runs no simulation and computes no statistic of its own: every
recomputed value comes from `verify_numbers.py`, which in turn uses only
`swarm_harness.stats`.

    python scripts/check_section13.py            the table
    python scripts/check_section13.py --json     the same, as JSON

Exit status is 0 when every §13 row that `verify_numbers.py` covers is matched or
explained, 1 otherwise. "Explained" means the script deliberately recomputes a
statistic §13 retired; those rows are listed under RETIRED-STATISTIC and are a
finding about the script, not about the record.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# Rows where verify_numbers.py's `claimed` string is the PRE-Phase-A statistic.
# Listed explicitly rather than detected, so adding one is a deliberate act:
# each entry names the §12.1 D0 line that retired it.
RETIRED = {
    27: "D0: mechanism peak, ratio of medians -> paired (2.21 -> 2.149)",
    28: "D0: §7 hold ratios, ratio of medians -> paired",
    29: "D0: §7 hold ratios, ratio of medians -> paired",
    30: "D0: §7 hold ratios, ratio of medians -> paired",
    34: "D0: survival, median run-level -> mean per-robot with Wilson",
    35: "D0: survival, median run-level -> mean per-robot with Wilson",
    36: "D0: survival, median run-level -> mean per-robot with Wilson",
    37: "D0: survival, median run-level -> mean per-robot with Wilson",
    46: "D0: survival at 0.47 R, median run-level -> mean per-robot with Wilson",
    67: "D0: Pareto survival, median run-level -> mean per-robot with Wilson",
}

# Rows whose ids are crossed between the two documents: `verify_numbers.py`
# item N recomputes the quantity §13 lists under row M. Recorded as a pair so
# the check can confirm the crossing rather than merely tolerate a mismatch.
CROSSED = {71: 72, 72: 71}

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def numbers(text: str) -> list[float]:
    """Every number in a cell, in order, so formatting differences do not matter."""
    return [float(m) for m in _NUM.findall(text.replace("−", "-").replace(",", " "))]


def matches(claimed: str, recomputed: str, tol: float = 0.02) -> bool:
    """Do the §13 value's numbers all appear, in order, in the recomputed cell?

    §13 quotes point estimates to a stated number of digits and often omits the
    interval that the recomputation prints, so this checks that §13's numbers are
    a prefix-matched subsequence of the recomputed ones within a relative
    tolerance -- 2%, which is wider than bootstrap re-seeding noise and narrower
    than any disagreement worth reporting.
    """
    want, got = numbers(claimed), numbers(recomputed)
    if not want:
        return False
    j = 0
    for w in want:
        while j < len(got):
            g = got[j]
            j += 1
            if abs(g - w) <= tol * max(1e-9, abs(w)):
                break
        else:
            return False
    return True


def main() -> int:
    section13 = {n["id"]: n for n in json.loads((REPO / "docs" / "paper-source.json").read_text())["numbers"]}
    proc = subprocess.run([sys.executable, str(REPO / "scripts" / "verify_numbers.py"), "--json"],
                          capture_output=True, text=True, cwd=REPO)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return 1
    recomputed = json.loads(proc.stdout)

    out = []
    for r in recomputed:
        row = section13.get(r["id"])
        want = "" if row is None else f"{row['value']}" + (f"  {row['ci']}" if row.get("ci") else "")
        got = str(r["recomputed"])
        if got == "ERROR":
            verdict = "ERROR"
        elif row is None:
            verdict = "NOT IN §13"
        elif matches(want, got):
            verdict = "MATCH"
        elif r["id"] in CROSSED and matches(
                f"{section13[CROSSED[r['id']]]['value']}", got):
            verdict = "MATCH (crossed id)"
        elif r["id"] in RETIRED:
            verdict = "RETIRED-STATISTIC"
        else:
            verdict = "MISMATCH"
        note = r["note"]
        if r["id"] in RETIRED:
            note = RETIRED[r["id"]]
        elif verdict == "MATCH (crossed id)":
            note = (f"recomputes the quantity §13 lists as row {CROSSED[r['id']]}; "
                    "the two ids are swapped between the documents")
        out.append(dict(id=r["id"], quantity="" if row is None else row["quantity"],
                        section13=want, verify_numbers_claimed=r["claimed"],
                        recomputed=got, verdict=verdict, note=note))

    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
    else:
        print(f"{'#':>4}  {'verdict':<18}  {'§13':<32}  {'recomputed':<44}  note")
        for r in out:
            print(f"{r['id']:>4}  {r['verdict']:<18}  {r['section13'][:32]:<32}  "
                  f"{r['recomputed'][:44]:<44}  {r['note'][:70]}")
        tally: dict[str, int] = {}
        for r in out:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        print("\n" + "  ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
        print(f"{len(out)} of {len(section13)} §13 rows are covered by verify_numbers.py.")
    return 0 if not any(r["verdict"] in ("MISMATCH", "ERROR") for r in out) else 1


if __name__ == "__main__":
    raise SystemExit(main())
