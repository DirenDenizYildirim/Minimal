"""Figures.

Build doc, section 2.3: the deliverable is **not** a one-step frontier. For each
capability row we plot the performance surface over the hostility dial(s), then
draw the threshold contours ``P = T`` on it. Several contours on one panel
(T = 0.7, 0.8, 0.9) show how the "minimum" depends on where the bar is set. The
frontier ``c*(theta)`` is then read off as the lowest row whose contour still
encloses theta.

Every figure drawn from a non-enumerated row carries an upper-bound stamp. That
is not decoration: "no controller found meeting T" means *not found*, not *not
possible*, and a figure that does not say so is making a claim we cannot support.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .load import Records  # noqa: E402
from .stats import median_ci  # noqa: E402

UPPER_BOUND_NOTE = (
    "Rows marked † are not exhaustively searched: their minima are UPPER BOUNDS "
    "(not found ≠ not possible)."
)


def _stamp(fig, records: Records, y: float = 0.005) -> None:
    """Mark the figure when any row on it is an upper bound rather than a minimum."""
    if records.any_upper_bound():
        fig.text(
            0.5,
            y,
            UPPER_BOUND_NOTE,
            ha="center",
            va="bottom",
            fontsize=7.5,
            style="italic",
            color="#8a3b00",
        )


def _row_is_bounded(sub: Records) -> bool:
    return sub.any_upper_bound()


def _label(name: str, sub: Records) -> str:
    return f"{name} †" if _row_is_bounded(sub) else str(name)


def curve(
    records: Records,
    x: str,
    metric: str,
    group: Sequence[str] = ("row",),
    thresholds: Sequence[float] = (),
    out: str | Path | None = None,
    title: str | None = None,
    ylabel: str | None = None,
):
    """Performance against a single hostility dial, one line per capability row.

    Medians with bootstrap CI bands. Threshold lines are drawn horizontally: the
    dial value where a line crosses `T` is that row's tolerance for this dial.
    """
    group = [g for g in group if g in records.fields()]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    groups = records.group_by(group) if group else {(): records}
    for key, sub in sorted(groups.items(), key=lambda kv: str(kv[0])):
        xs = sub.unique(x)
        med, lo, hi = [], [], []
        for xv in xs:
            cell = sub.filter(**{x: xv})
            m, l, h = median_ci(cell.column(metric))
            med.append(m)
            lo.append(l)
            hi.append(h)
        name = ", ".join(f"{k}={v}" for k, v in zip(group, key)) if group else metric
        line, = ax.plot(xs, med, marker="o", markersize=4, label=_label(name, sub))
        ax.fill_between(xs, lo, hi, alpha=0.18, color=line.get_color(), linewidth=0)

    for t in thresholds:
        ax.axhline(t, color="0.35", linestyle="--", linewidth=0.9)
        ax.annotate(
            f"T = {t:g}",
            xy=(1.0, t),
            xycoords=("axes fraction", "data"),
            xytext=(3, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color="0.3",
        )

    ax.set_xlabel(x)
    ax.set_ylabel(ylabel or metric)
    ax.set_title(title or f"{metric} vs {x}", fontsize=10, wrap=True)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _stamp(fig, records)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=160)
    return fig


def surface(
    records: Records,
    x: str,
    y: str,
    metric: str,
    row_key: str = "row",
    thresholds: Sequence[float] = (0.7, 0.8, 0.9),
    out: str | Path | None = None,
    title: str | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
):
    """The section-2.3 figure: one performance surface per capability row, with
    threshold contours drawn on it."""
    rows = records.group_by([row_key]) if row_key in records.fields() else {(metric,): records}
    rows = dict(sorted(rows.items(), key=lambda kv: str(kv[0])))

    n = len(rows)
    # A single panel still needs room for a title and the colorbar, so the width
    # has a floor rather than scaling straight from the panel count.
    fig, axes = plt.subplots(1, n, figsize=(max(7.5, 5.0 * n), 4.6), squeeze=False)
    axes = axes[0]

    grids = {}
    for (name,), sub in rows.items():
        xs, ys = sub.unique(x), sub.unique(y)
        z = np.full((len(ys), len(xs)), np.nan)
        for i, yv in enumerate(ys):
            for j, xv in enumerate(xs):
                cell = sub.filter(**{x: xv, y: yv})
                if len(cell):
                    z[i, j] = float(np.median(np.asarray(cell.column(metric), dtype=float)))
        grids[name] = (np.asarray(xs, dtype=float), np.asarray(ys, dtype=float), z, sub)

    if vmin is None:
        vmin = min(np.nanmin(g[2]) for g in grids.values())
    if vmax is None:
        vmax = max(np.nanmax(g[2]) for g in grids.values())

    mesh = None
    for ax, (name, (xs, ys, z, sub)) in zip(axes, grids.items()):
        mesh = ax.pcolormesh(xs, ys, z, shading="nearest", vmin=vmin, vmax=vmax, cmap="viridis")
        levels = [t for t in sorted(thresholds) if np.nanmin(z) < t < np.nanmax(z)]
        if levels:
            cs = ax.contour(xs, ys, z, levels=levels, colors="white", linewidths=1.4)
            ax.clabel(cs, fmt="T=%.2g", fontsize=8, colors="white")
        missed = [t for t in thresholds if t not in levels]
        if missed:
            ax.text(
                0.02,
                0.02,
                "no contour for T = " + ", ".join(f"{t:g}" for t in missed),
                transform=ax.transAxes,
                fontsize=7.5,
                color="white",
                va="bottom",
            )
        ax.set_title(_label(name, sub), fontsize=10)
        ax.set_xlabel(x)
        ax.set_ylabel(y)

    fig.suptitle(title or f"{metric} over ({x}, {y})", fontsize=10, wrap=True)
    # Reserve room around the axes before the colorbar is attached: under them
    # so the upper-bound stamp cannot land on the tick labels, and at the right
    # so the colorbar and its label are not clipped.
    fig.subplots_adjust(bottom=0.22, top=0.86, right=0.88)
    if mesh is not None:
        fig.colorbar(mesh, ax=list(axes), label=metric, fraction=0.03, pad=0.02)
    _stamp(fig, records, y=0.02)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=160)
    return fig
