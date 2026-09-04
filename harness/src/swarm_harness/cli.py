"""``swarm-figure`` — tables and figures from a sweep's JSONL output."""

from __future__ import annotations

import argparse
import sys

from .load import load_jsonl
from .stats import fraction_meeting, summarise


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("input", help="JSONL produced by `swarm sweep` or `swarm run`")
    p.add_argument("--metric", default="final_largest_cluster_fraction")
    p.add_argument("--out", default=None, help="output image path")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="swarm-figure", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("table", help="medians with bootstrap CIs, grouped by cell")
    _add_common(t)
    t.add_argument("--by", nargs="+", required=True, help="fields to group by")
    t.add_argument("--threshold", type=float, default=None, help="also report the share of runs meeting T")

    c = sub.add_parser("curve", help="performance against one hostility dial")
    _add_common(c)
    c.add_argument("--x", required=True)
    c.add_argument("--group", nargs="*", default=["row"])
    c.add_argument("--thresholds", nargs="*", type=float, default=[])
    c.add_argument("--title", default=None)

    s = sub.add_parser("surface", help="performance surface with threshold contours")
    _add_common(s)
    s.add_argument("--x", required=True)
    s.add_argument("--y", required=True)
    s.add_argument("--row-key", default="row")
    s.add_argument("--thresholds", nargs="*", type=float, default=[0.7, 0.8, 0.9])
    s.add_argument("--title", default=None)

    args = parser.parse_args(argv)
    records = load_jsonl(args.input)

    if args.command == "table":
        missing = [b for b in args.by if b not in records.fields()]
        if missing:
            parser.error(f"no such field(s): {', '.join(missing)}")
        groups = records.group_by(args.by)
        width = max(len(" ".join(f"{k}={v}" for k, v in zip(args.by, key))) for key in groups)
        header = f"{'cell'.ljust(width)}  {'n':>5}  {'median [95% CI]':>28}"
        if args.threshold is not None:
            header += f"  {'P>=T':>6}"
        header += "  bound"
        print(header)
        print("-" * len(header))
        for key in sorted(groups, key=lambda k: tuple(str(v) for v in k)):
            sub = groups[key]
            values = sub.column(args.metric)
            stat = summarise(values)
            label = " ".join(f"{k}={v}" for k, v in zip(args.by, key))
            line = (
                f"{label.ljust(width)}  {stat.n:5d}  "
                f"{stat.median:9.4g} [{stat.lo:8.4g}, {stat.hi:8.4g}]"
            )
            if args.threshold is not None:
                line += f"  {fraction_meeting(values, args.threshold):6.2f}"
            line += "  upper" if sub.any_upper_bound() else "  tight"
            print(line)
        if records.any_upper_bound():
            print(
                "\nnote: rows marked 'upper' are not exhaustively searched — their "
                "minima are UPPER BOUNDS.\n      Rows: " + ", ".join(records.upper_bound_rows())
            )
        return 0

    from . import plot  # imported late so `table` does not need matplotlib

    if args.command == "curve":
        plot.curve(
            records,
            x=args.x,
            metric=args.metric,
            group=args.group,
            thresholds=args.thresholds,
            out=args.out,
            title=args.title,
        )
    else:
        plot.surface(
            records,
            x=args.x,
            y=args.y,
            metric=args.metric,
            row_key=args.row_key,
            thresholds=args.thresholds,
            out=args.out,
            title=args.title,
        )
    if args.out:
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
