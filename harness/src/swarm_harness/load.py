"""Read the simulator's JSONL output."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


def _flatten(record: dict[str, Any]) -> dict[str, Any]:
    """Flatten the nested parts of a run record into plain columns.

    ``cell`` holds the sweep coordinates and is promoted to top level so a
    coordinate can be addressed by the same dotted path the sweep file used
    (``occlusion.fn_rate``). ``capability`` becomes ``capability.S`` and friends.
    ``series`` is left alone; it is a list, not a column.
    """
    flat = {k: v for k, v in record.items() if k not in ("cell", "capability")}
    for key, value in record.get("cell", {}).items():
        flat[key] = value
    cap = record.get("capability")
    if cap:
        flat["capability.S"] = cap["sensor_states"]
        flat["capability.M"] = cap["memory_bits"]
        flat["capability.A"] = int(cap["arithmetic"])
        flat["capability.K"] = cap["comm_bits"]
        flat["capability"] = (
            f"({cap['sensor_states']},{cap['memory_bits']},"
            f"{int(cap['arithmetic'])},{cap['comm_bits']})"
        )
    return flat


@dataclass(frozen=True)
class Records:
    """A sweep's trials, as flat dictionaries."""

    rows: list[dict[str, Any]]

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.rows)

    def column(self, name: str) -> list[Any]:
        try:
            return [r[name] for r in self.rows]
        except KeyError:
            raise KeyError(
                f"no field {name!r}; available: {', '.join(sorted(self.fields()))}"
            ) from None

    def fields(self) -> set[str]:
        out: set[str] = set()
        for r in self.rows:
            out.update(r)
        return out

    def unique(self, name: str) -> list[Any]:
        """Distinct values of a field, in sorted order where that is possible."""
        seen = list(dict.fromkeys(self.column(name)))
        try:
            return sorted(seen)
        except TypeError:
            return seen

    def group_by(self, keys: Sequence[str]) -> dict[tuple, "Records"]:
        buckets: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        for r in self.rows:
            buckets[tuple(r.get(k) for k in keys)].append(r)
        return {k: Records(v) for k, v in buckets.items()}

    def filter(self, **equals: Any) -> "Records":
        return Records([r for r in self.rows if all(r.get(k) == v for k, v in equals.items())])

    def any_upper_bound(self) -> bool:
        """True if any trial came from a row whose minimum is not tight.

        Every figure drawn from such a sweep has to say so: 'no controller found
        meeting T' means *not found*, not *not possible*.
        """
        return any(not r.get("minimum_is_tight", True) for r in self.rows)

    def upper_bound_rows(self) -> list[str]:
        labels = {
            str(r.get("row", r.get("capability", "?")))
            for r in self.rows
            if not r.get("minimum_is_tight", True)
        }
        return sorted(labels)

    def provenance(self) -> str | None:
        """The single provenance in these records, or None if they disagree."""
        seen = {r.get("provenance") for r in self.rows}
        return seen.pop() if len(seen) == 1 else None

    def mark(self) -> str:
        """Figure marker for how this row's controller was obtained.

        A searched row and a hand-written one are both upper bounds, but they
        are not the same claim: a search that failed to find something is weak
        evidence that nothing is there, while a hand-written guess is no
        evidence at all. Conflating them is how "more sensing hurts" gets
        written down.

        ``†`` searched but not exhaustive; ``‡`` hand-designed; nothing for an
        enumerated row, whose minimum is tight.
        """
        return {"optimiser_found": " †", "hand_designed": " ‡"}.get(self.provenance() or "", "")


def load_jsonl(path: str | Path | Iterable[str]) -> Records:
    """Load run records from a JSONL file, or from any iterable of JSON lines."""
    if isinstance(path, (str, Path)):
        with open(path, "r", encoding="utf-8") as fh:
            lines: Iterable[str] = list(fh)
    else:
        lines = path
    rows = [_flatten(json.loads(line)) for line in lines if line.strip()]
    if not rows:
        raise ValueError("no records found")
    return Records(rows)
