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
from .stats import median_ci, proportion_ci  # noqa: E402

UPPER_BOUND_NOTE = (
    "† searched, not exhaustive — an upper bound.    "
    "‡ hand-designed, not searched — no evidence about the capability itself."
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


def _label(name: str, sub: Records) -> str:
    """Row label with its provenance marker. See `Records.mark`."""
    return f"{name}{sub.mark()}"


def annotate_params(fig, records: Records, fields: Sequence[str] = (), y: float = 0.955) -> None:
    """Print the run parameters a reader needs to interpret the figure.

    A pursuit result is meaningless without the speed ratio, the handling time,
    the swarm size, the trial length and the arena the swarm started in — those
    set what "survival" even means. Anything constant across the records is
    printed; anything that varies is a swept axis and is on the plot already.
    """
    parts = []
    for f in fields:
        values = {r.get(f) for r in records if f in r}
        if len(values) == 1:
            v = values.pop()
            if v is not None:
                parts.append(f"{_PARAM_LABELS.get(f, f)} = {v:g}" if isinstance(v, (int, float))
                             else f"{_PARAM_LABELS.get(f, f)} = {v}")
    if parts:
        fig.text(0.5, y, "   ".join(parts), ha="center", va="top",
                 fontsize=8, color="0.3")


_PARAM_LABELS = {
    "pursuer_speed_ratio": "ρ",
    "pursuer_handling_time": "h",
    "n": "n",
    "duration": "τ",
    "start_radius": "start radius",
}


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
    baseline_y=None,
    annotate: Sequence[str] = (),
):
    """The section-2.3 figure: one performance surface per capability row, with
    threshold contours drawn on it.

    ``baseline_y`` names a value of the `y` dial that is the control condition —
    typically the dial turned off. Each column is then divided by its own value
    there, so the surface shows *degradation relative to that row's own
    baseline* rather than raw performance.

    Use it whenever the rows differ on clean ground. Rows that vary the
    controller's own constants do: in the H2 sweep the largest-R0 row aggregates
    poorly with no terrain at all, and on a shared raw colour scale it swamps
    every other panel while saying nothing about terrain. Normalising is not
    cosmetic there — the comparison is meaningless without it.
    """
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
        if baseline_y is not None:
            if baseline_y not in ys:
                raise ValueError(
                    f"baseline_y={baseline_y!r} is not a value of {y}; have {ys}"
                )
            base = z[ys.index(baseline_y), :]
            with np.errstate(divide="ignore", invalid="ignore"):
                z = np.where(base == 0, np.nan, z / base)
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

    label = metric if baseline_y is None else f"{metric} / value at {y}={baseline_y}"
    caption = title or f"{label} over ({x}, {y})"
    # Height for the caption scales with how many lines it has: a figure five
    # panels wide will not wrap a long title on its own, it will just overrun.
    caption_lines = caption.count("\n") + 1
    fig.suptitle(caption, fontsize=9.5, wrap=True, y=0.985, va="top")
    # Reserve room around the axes before the colorbar is attached: under them
    # so the upper-bound stamp cannot land on the tick labels, and at the right
    # so the colorbar and its label are not clipped.
    top = 0.93 - 0.045 * caption_lines - (0.04 if annotate else 0.0)
    fig.subplots_adjust(bottom=0.22, top=top, right=0.88)
    if annotate:
        annotate_params(fig, records, annotate)
    if mesh is not None:
        fig.colorbar(mesh, ax=list(axes), label=label, fraction=0.03, pad=0.02)
    _stamp(fig, records, y=0.02)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=160)
    return fig


def paired_panels(
    records: Records,
    x: str,
    metrics: Sequence[tuple],
    col_field: str | None = None,
    group: Sequence[str] = ("row",),
    out: str | Path | None = None,
    title: str | None = None,
    annotate: Sequence[str] = (),
):
    """A grid of panels: one panel-row per metric, one panel-column per value of
    `col_field`, one line per capability row, with bootstrap CI bands.

    Built for questions that two metrics answer differently. Whether a swarm
    *reaches* a connected cluster and how tightly it *holds* one are not the same
    measurement, and terrain moves them apart — showing only one of them picks
    the answer before the reader sees it.

    ``metrics`` entries are ``(field, label, baseline_x)``, optionally with a
    fourth element ``"proportion"`` for 0/1 outcomes. A non-None ``baseline_x``
    normalises each line by its own value at that `x`, which is how a
    ratio-to-flat-ground is drawn without letting rows that differ on clean
    ground masquerade as differing under terrain.

    Use ``"proportion"`` for anything boolean. Its median is 1 whenever the
    majority succeed, so a median panel draws a flat line at 1 while the
    underlying probability falls.
    """
    cols = records.unique(col_field) if col_field else [None]
    n_rows, n_cols = len(metrics), len(cols)
    # Reserve fixed *inches* for the title, the parameter line, the legend and
    # the provenance stamp, then convert to fractions. Fractional margins alone
    # collapse onto the axis labels when there is only one panel-row.
    top_in, bottom_in = (1.0 if annotate else 0.75), 1.15
    fig_h = 3.4 * n_rows + top_in + bottom_in
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(4.2 * n_cols, fig_h),
        squeeze=False,
        sharex=True,
    )

    group = [g for g in group if g in records.fields()]
    handles: dict[str, object] = {}
    for ri, spec in enumerate(metrics):
        field, label, baseline_x = spec[0], spec[1], spec[2]
        summarise = proportion_ci if (len(spec) > 3 and spec[3] == "proportion") else median_ci
        for ci, cv in enumerate(cols):
            ax = axes[ri][ci]
            sub_all = records.filter(**{col_field: cv}) if col_field else records
            for key, sub in sorted(
                (sub_all.group_by(group) if group else {(): sub_all}).items(),
                key=lambda kv: str(kv[0]),
            ):
                xs = sub.unique(x)
                base = 1.0
                if baseline_x is not None:
                    cell = sub.filter(**{x: baseline_x})
                    base = float(np.median(np.asarray(cell.column(field), dtype=float)))
                med, lo, hi = [], [], []
                for xv in xs:
                    vals = np.asarray(sub.filter(**{x: xv}).column(field), dtype=float) / base
                    m, l, h = summarise(vals)
                    med.append(m)
                    lo.append(l)
                    hi.append(h)
                name = _label(", ".join(str(v) for v in key) if group else field, sub)
                line, = ax.plot(xs, med, marker="o", markersize=3.5, label=name)
                ax.fill_between(xs, lo, hi, alpha=0.18, color=line.get_color(), linewidth=0)
                handles.setdefault(name, line)
            if ri == 0 and col_field:
                ax.set_title(f"{col_field} = {cv:g}" if isinstance(cv, float) else f"{col_field} = {cv}",
                             fontsize=9)
            if ci == 0:
                ax.set_ylabel(label, fontsize=9)
            if ri == n_rows - 1:
                ax.set_xlabel(x)
            ax.grid(alpha=0.25, linewidth=0.6)

    fig.subplots_adjust(bottom=bottom_in / fig_h, top=1.0 - top_in / fig_h)
    fig.legend(
        list(handles.values()),
        list(handles.keys()),
        loc="lower center",
        ncol=min(4, len(handles)),
        fontsize=8,
        frameon=False,
        bbox_to_anchor=(0.5, 0.36 / fig_h),
    )
    fig.suptitle(title or "", fontsize=10, wrap=True, y=1.0 - 0.22 / fig_h)
    if annotate:
        annotate_params(fig, records, annotate, y=1.0 - 0.62 / fig_h)
    _stamp(fig, records, y=0.05 / fig_h)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=160)
    return fig
