"""Summary statistics for a sweep cell.

The protocol the build doc adopts (Birattari lab / ANTS) is medians with
confidence intervals and a non-parametric test across capability rows. Run
counts are >= 100 per cell for Tier 1 and >= 30 for Tier 2.

Medians rather than means: performance distributions in a cell are routinely
bimodal — the swarm either aggregates or it does not — and a mean lands between
the two modes where no run ever sits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Summary:
    n: int
    median: float
    lo: float
    hi: float
    mean: float
    std: float

    def __str__(self) -> str:
        return f"{self.median:.4g} [{self.lo:.4g}, {self.hi:.4g}] (n={self.n})"


def bootstrap_ci(
    values: Sequence[float],
    statistic=np.median,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap CI for `statistic`.

    Deterministic: the seed is fixed so a figure regenerates identically.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (float("nan"), float("nan"))
    if v.size == 1:
        return (float(v[0]), float(v[0]))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(resamples, v.size))
    stats = statistic(v[idx], axis=1)
    alpha = (1.0 - confidence) / 2.0
    lo, hi = np.quantile(stats, [alpha, 1.0 - alpha])
    return (float(lo), float(hi))


def median_ci(values: Sequence[float], **kw) -> tuple[float, float, float]:
    """Median with its bootstrap CI, as ``(median, lo, hi)``."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        nan = float("nan")
        return (nan, nan, nan)
    lo, hi = bootstrap_ci(v, **kw)
    return (float(np.median(v)), lo, hi)


def summarise(values: Sequence[float], **kw) -> Summary:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        nan = float("nan")
        return Summary(0, nan, nan, nan, nan, nan)
    med, lo, hi = median_ci(v, **kw)
    return Summary(int(v.size), med, lo, hi, float(v.mean()), float(v.std(ddof=1)) if v.size > 1 else 0.0)


def fraction_meeting(values: Sequence[float], threshold: float, higher_is_better: bool = True) -> float:
    """Share of runs in a cell that met the task threshold ``T``.

    This is the quantity a threshold contour is drawn on when performance is
    scored per run rather than per cell.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan")
    return float(np.mean(v >= threshold) if higher_is_better else np.mean(v <= threshold))


def friedman_across_rows(per_row: dict[str, Sequence[float]]):
    """Friedman test across capability rows on matched cells.

    Requires SciPy (``pip install 'swarm-harness[stats]'``). Raises a clear error
    rather than silently reporting something weaker, because the venue expects
    this specific test.
    """
    try:
        from scipy.stats import friedmanchisquare
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "the Friedman test needs SciPy: pip install 'swarm-harness[stats]'"
        ) from exc
    labels = list(per_row)
    if len(labels) < 3:
        raise ValueError("the Friedman test needs at least three rows")
    lengths = {len(per_row[k]) for k in labels}
    if len(lengths) != 1:
        raise ValueError(f"rows must be matched on the same cells, got lengths {lengths}")
    return friedmanchisquare(*[np.asarray(per_row[k], dtype=float) for k in labels])


def wilson_ci(values, confidence: float = 0.95):
    """Observed proportion with a **Wilson score interval**.

    Wilson rather than bootstrap, because a proportion is not a mean of a
    continuous quantity and the bootstrap fails exactly where these experiments
    live. Resampling 100 successes out of 100 gives 100 successes every time, so
    the bootstrap reports a zero-width interval at p = 1 — the most confident
    possible claim from the data least able to support it. Wilson stays
    asymmetric and finite at both boundaries.

    Returns ``(p, lo, hi)``. Also the reason not to take a *median* of a 0/1
    outcome: the median is 1 whenever the majority succeed, which draws a flat
    line while the probability falls.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    n = v.size
    if n == 0:
        nan = float("nan")
        return (nan, nan, nan)
    p = float(v.mean())
    # Two-sided normal quantile; 1.959964 at 95%, and the common alternatives are
    # spelled out rather than pulling in SciPy for one number.
    z = {0.90: 1.644854, 0.95: 1.959964, 0.99: 2.575829}.get(confidence)
    if z is None:
        raise ValueError(f"confidence {confidence} not tabulated; use 0.90, 0.95 or 0.99")
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, float(max(0.0, centre - half)), float(min(1.0, centre + half)))


def proportion_ci(values, confidence: float = 0.95, **_ignored):
    """Alias for :func:`wilson_ci`, kept so callers read as intent."""
    return wilson_ci(values, confidence=confidence)
