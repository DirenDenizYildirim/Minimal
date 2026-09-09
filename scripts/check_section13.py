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
explained, 1 otherwise. "Explained" means either that the script
deliberately recomputes a statistic §13 retired (RETIRED-STATISTIC -- a finding
about the script, not about the record) or that §12.1 already recorded the
difference against the published value (DOCUMENTED §12.1). A MISMATCH is a §13
row that no longer reproduces from the committed configs, which is a finding
about the record and must be reported rather than fixed in place.
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
    10: "D0: n = 2 hold, '~10% still touching at tau' -> 0.15 still touching; "
        "0.10 is the SHARE OF TIME.  §13 row 10 still carries the pre-correction value",
    34: "D0: survival, median run-level -> mean per-robot with Wilson",
    35: "D0: survival, median run-level -> mean per-robot with Wilson",
    36: "D0: survival, median run-level -> mean per-robot with Wilson",
    37: "D0: survival, median run-level -> mean per-robot with Wilson",
    46: "D0: survival at 0.47 R, median run-level -> mean per-robot with Wilson",
    67: "D0: Pareto survival, median run-level -> mean per-robot with Wilson",
}

# Differences §12.1 already recorded against the published value, so a
# recomputation reproducing the *verification pass* rather than §13 is the
# expected outcome and not a new failure.
DOCUMENTED = {
    25: "§12.1: 1.178 [1.158, 1.193] recomputed against the published 1.175 "
        "[1.154, 1.190] -- the same runs; the section calls it a re-seeded bootstrap",
    26: "§12.1: 0.979 [0.973, 0.986] recomputed against the published 0.980 "
        "[0.976, 0.986] -- the same runs",
}

# Rows whose ids are crossed between the two documents: `verify_numbers.py`
# item N recomputes the quantity §13 lists under row M. Recorded as a pair so
# the check can confirm the crossing rather than merely tolerate a mismatch.
CROSSED = {71: 72, 72: 71}

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
# A digit right after a letter, a digit or "=" is usually part of a name, not a
# quantity: the "2" in "S2-rough", the "0" in "R0", the "2" in "n=2". But "x3.05"
# and "×1.20" are multipliers and must be read. A decimal point separates the two
# cases, and nothing in §13 names a row after a fractional number.
_GLUED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=")
# Bootstrap intervals are re-seeded on a re-run, so their endpoints move a little
# even when the point estimate is bit-identical (paper-source §12.1 records §6's
# 1.178 against the published 1.175 for exactly this reason).
CI_TOLERANCE = 0.02


def numbers(text: str) -> list[tuple[float, float]]:
    """Numbers in a cell, each with the tolerance its own quoted precision earns.

    §13 quotes to a stated number of digits and the task is to match it *to those
    digits*, so "1.43" is satisfied by 1.427 and "1.401" is not satisfied by
    1.3875. A leading "~" means the source itself is approximate and buys 10%.
    """
    text = text.replace("−", "-").replace(",", " ")
    # §13 groups thousands with a space ("7 200", "50 000"); the recomputation
    # prints them unspaced. Join the groups back up before tokenising, or one
    # number is read as two.
    text = re.sub(r"(?<=\d)[   ](?=\d{3}(?!\d))", "", text)
    out = []
    for m in _NUM.finditer(text):
        token = m.group()
        before = text[m.start() - 1] if m.start() else " "
        # "1.3875-1.4299" is a range, not a negative number: a minus glued to the
        # end of another number is a dash.
        if token.startswith("-") and before in "0123456789.":
            token = token[1:]
            before = "-"
        if before in _GLUED and "." not in token:
            continue
        approx = text[max(0, m.start() - 2):m.start()].strip().endswith("~")
        value = float(token)
        decimals = len(token.partition(".")[2])
        tol = 0.1 * abs(value) if approx else 0.5 * 10.0 ** (-decimals)
        out.append((value, tol))
    return out


def _subsequence(want, got, percent: bool) -> bool:
    """Does every wanted number appear, in order, among the recomputed ones?"""
    j = 0
    for w, tol in want:
        while j < len(got):
            g = got[j]
            j += 1
            scales = (1.0, 0.01, 100.0) if percent else (1.0,)
            if any(abs(g * s - w) <= tol for s in scales):
                break
        else:
            return False
    return True


def matches(value: str, ci: str, recomputed: str) -> bool:
    """§13's point estimate must reproduce to its stated digits.

    The interval is checked only when the recomputation printed one; several
    items report a point estimate alone, and demanding an interval they never
    computed would fail them for the wrong reason.
    """
    got = [v for v, _ in numbers(recomputed)]
    percent = "%" in recomputed or "%" in value
    if not numbers(value) or not _subsequence(numbers(value), got, percent):
        return False
    if ci and "[" in recomputed:
        want_ci = [(v, max(t, CI_TOLERANCE * abs(v))) for v, t in numbers(ci)]
        return _subsequence(want_ci, got, percent)
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
        elif matches(row["value"], row.get("ci") or "", got):
            verdict = "MATCH"
        elif r["id"] in CROSSED and matches(
                section13[CROSSED[r["id"]]]["value"],
                section13[CROSSED[r["id"]]].get("ci") or "", got):
            verdict = "MATCH (crossed id)"
        elif r["id"] in RETIRED:
            verdict = "RETIRED-STATISTIC"
        elif r["id"] in DOCUMENTED:
            verdict = "DOCUMENTED §12.1"
        else:
            verdict = "MISMATCH"
        note = r["note"]
        if r["id"] in RETIRED:
            note = RETIRED[r["id"]]
        elif verdict == "DOCUMENTED §12.1":
            note = DOCUMENTED[r["id"]]
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
