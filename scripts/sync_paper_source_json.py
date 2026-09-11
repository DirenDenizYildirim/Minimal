#!/usr/bin/env python3
"""Regenerate `docs/paper-source.json`'s §13 `numbers` array from the markdown.

`docs/paper-source.md` §13 is the authority; `docs/paper-source.json` is the
machine-readable mirror that `check_section13.py` and `check_draft_against_source.py`
read. Until freeze lift 1 the two were maintained by hand, which is how §13's
rows 71 and 72 came to be crossed against `verify_numbers.py` and how a
correction to the markdown could leave the JSON stale.

    python scripts/sync_paper_source_json.py           rewrite the numbers array
    python scripts/sync_paper_source_json.py --check   exit non-zero if stale

Only the `numbers` array is touched. Everything else in the JSON -- the claims
register, the ledger, the freeze block -- is left exactly as it is, because those
are not derived from a table and a parser that rewrote them would be inventing
structure rather than mirroring it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MD = REPO / "docs" / "paper-source.md"
JSON = REPO / "docs" / "paper-source.json"

# The last cell is the commit (or several, and sometimes a note beside them),
# so it is taken whole and the backticks stripped rather than matched as one
# identifier: several rows cite two commits and one now cites a correction.
ROW = re.compile(r"^\|\s*(\d+)\s*\|(.*)\|([^|]*)\|\s*$")


def parse() -> list[dict]:
    """Every `| id | quantity | value | ci | unit | source | commit |` row of §13.

    §13 is the only part of the document whose rows start with a bare integer id,
    so the section is found by its heading and read to the next one.
    """
    text = MD.read_text()
    start = text.index("## 13. Numbers to quote")
    end = text.index("\n## ", start + 10)
    out, seen = [], set()
    for line in text[start:end].split("\n"):
        m = ROW.match(line)
        if not m:
            continue
        nid = int(m.group(1))
        # Split on unescaped pipes only: the constants rows carry `\|` inside a
        # cell to separate state 0 from state 1, and splitting on those would
        # shear the row into the wrong number of fields.
        parts = [c.strip() for c in re.split(r"(?<!\\)\|", m.group(2))]
        if len(parts) != 5:
            raise SystemExit(f"§13 row {nid} has {len(parts)} fields, not 5: {line}")
        quantity, value, ci, unit, source = parts
        if nid in seen:
            raise SystemExit(f"§13 has two rows with id {nid}")
        seen.add(nid)
        nul = lambda v: None if v in ("—", "-", "") else v   # noqa: E731
        out.append(dict(id=nid, quantity=quantity, value=value, ci=nul(ci),
                        unit=nul(unit), source_section=source,
                        commit=m.group(3).strip().strip("`")))
    out.sort(key=lambda r: r["id"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    doc = json.loads(JSON.read_text())
    want = parse()
    if args.check:
        if doc["numbers"] == want:
            print(f"paper-source.json is in step with §13 ({len(want)} rows)")
            return 0
        have = {n["id"]: n for n in doc["numbers"]}
        got = {n["id"]: n for n in want}
        for nid in sorted(set(have) | set(got)):
            if have.get(nid) != got.get(nid):
                print(f"  {nid}: json {have.get(nid, {}).get('value')!r} "
                      f"vs §13 {got.get(nid, {}).get('value')!r}", file=sys.stderr)
        print(f"\npaper-source.json is stale against §13.", file=sys.stderr)
        return 1

    doc["numbers"] = want
    JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {len(want)} rows to {JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
