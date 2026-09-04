"""Aggregation and figures for the Tier-1 sweep output.

The simulator writes one JSON object per trial; everything here reads that
stream and turns it into the build doc's figure: a **performance surface** over
the hostility dials for each capability row, with threshold contours ``P = T``
drawn on it.

The surface, not a single frontier point, is the deliverable. Several contours
on one panel show how the "minimum" depends on where the bar is set, which is
the visual answer to the objection that minimality is ill-defined.
"""

from .load import Records, load_jsonl
from .stats import bootstrap_ci, median_ci, summarise

__all__ = ["Records", "load_jsonl", "bootstrap_ci", "median_ci", "summarise"]
