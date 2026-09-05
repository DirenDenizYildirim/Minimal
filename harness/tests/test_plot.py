import json
import unittest

import numpy as np
from matplotlib.collections import QuadMesh

from swarm_harness.load import load_jsonl


def _mesh_values(fig, xlabel):
    """The pcolormesh data from each data panel.

    Filters on the panel's x label, because `fig.axes` also holds the colorbar,
    which is itself a QuadMesh full of interpolated colour-scale values.
    """
    return [
        m.get_array().compressed()
        for a in fig.axes
        if a.get_xlabel() == xlabel
        for m in a.collections
        if isinstance(m, QuadMesh) and m.get_array() is not None
    ]
from swarm_harness import plot


def cells(rows, xs, ys, tight=True, provenance=None):
    if provenance is None:
        provenance = "enumerated" if tight else "optimiser_found"
    out = []
    for row in rows:
        for x in xs:
            for y in ys:
                for i in range(5):
                    out.append(
                        json.dumps(
                            {
                                "minimum_is_tight": tight,
                                "provenance": provenance,
                                "final_largest_cluster_fraction": max(0.0, 1.0 - x - 0.1 * y),
                                "cell": {"row": row, "occlusion.fn_rate": x, "swarm.n": y},
                            }
                        )
                    )
    return out


class TestPlot(unittest.TestCase):
    def test_curve_renders_and_labels_rows(self):
        r = load_jsonl(cells(["M0", "M1"], [0.0, 0.2, 0.4], [20]))
        fig = plot.curve(r, x="occlusion.fn_rate", metric="final_largest_cluster_fraction",
                         thresholds=[0.7, 0.9])
        ax = fig.axes[0]
        self.assertEqual(len(ax.get_lines()), 2 + 2)  # two rows, two threshold lines
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        self.assertTrue(any("M0" in l for l in labels))
        self.assertFalse(any("†" in l for l in labels), "tight rows must not be stamped")

    def test_searched_and_hand_designed_rows_are_marked_differently(self):
        # A search that found nothing is weak evidence; a hand-written guess is
        # none at all. The figure must not let them look alike.
        searched = load_jsonl(cells(["M1"], [0.0, 0.2], [20], tight=False,
                                    provenance="optimiser_found"))
        fig = plot.curve(searched, x="occlusion.fn_rate",
                         metric="final_largest_cluster_fraction")
        labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertTrue(any("†" in l for l in labels))
        self.assertFalse(any("‡" in l for l in labels))
        self.assertTrue(any("searched" in t.get_text() for t in fig.texts))

        hand = load_jsonl(cells(["B2"], [0.0, 0.2], [20], tight=False,
                                provenance="hand_designed"))
        fig = plot.curve(hand, x="occlusion.fn_rate",
                         metric="final_largest_cluster_fraction")
        labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertTrue(any("‡" in l for l in labels))
        self.assertFalse(any("†" in l for l in labels))

    def test_enumerated_rows_carry_no_marker(self):
        r = load_jsonl(cells(["M0"], [0.0, 0.2], [20], tight=True))
        fig = plot.curve(r, x="occlusion.fn_rate", metric="final_largest_cluster_fraction")
        labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertFalse(any("†" in l or "‡" in l for l in labels))

    def test_parameters_are_annotated_when_constant(self):
        import json as _json

        rows = [
            _json.dumps({
                "minimum_is_tight": True, "provenance": "enumerated",
                "survival_fraction": 0.5, "n": 20, "duration": 120.0,
                "pursuer_speed_ratio": 1.5, "pursuer_handling_time": h,
                "cell": {"row": "B0", "pursuer.range": 0.2, "pursuer.confusion": 0.0},
            })
            for h in (5.0, 5.0, 5.0)
        ]
        r = load_jsonl(rows)
        fig = plot.curve(r, x="pursuer.range", metric="survival_fraction")
        plot.annotate_params(fig, r, ["pursuer_speed_ratio", "pursuer_handling_time",
                                      "n", "duration"])
        text = " ".join(t.get_text() for t in fig.texts)
        self.assertIn("ρ = 1.5", text)
        self.assertIn("h = 5", text)
        self.assertIn("τ = 120", text)

    def test_surface_makes_one_panel_per_row_with_contours(self):
        r = load_jsonl(cells(["M0", "M1"], [0.0, 0.2, 0.4, 0.6], [10, 20, 50]))
        fig = plot.surface(r, x="occlusion.fn_rate", y="swarm.n",
                           metric="final_largest_cluster_fraction", thresholds=[0.5, 0.7])
        panels = [a for a in fig.axes if a.get_xlabel() == "occlusion.fn_rate"]
        self.assertEqual(len(panels), 2)
        self.assertEqual(panels[0].get_title(), "M0")

    def test_surface_reports_thresholds_it_could_not_draw(self):
        # A dial range where performance never crosses T must say so rather than
        # silently omitting the contour.
        r = load_jsonl(cells(["M0"], [0.0, 0.05], [20, 30]))
        fig = plot.surface(r, x="occlusion.fn_rate", y="swarm.n",
                           metric="final_largest_cluster_fraction", thresholds=[0.1])
        panel = [a for a in fig.axes if a.get_xlabel() == "occlusion.fn_rate"][0]
        self.assertTrue(any("no contour" in t.get_text() for t in panel.texts))


class TestBaselineNormalisation(unittest.TestCase):
    def _records(self):
        # Two rows with very different clean-ground performance but the SAME
        # relative response to the dial. Raw, they look nothing alike.
        import json

        out = []
        for row, scale in (("cheap", 1.0), ("expensive", 10.0)):
            for x in (0.1, 0.2):
                for y in (0.0, 0.5):
                    for _ in range(3):
                        out.append(
                            json.dumps(
                                {
                                    "minimum_is_tight": True,
                                    "final_dispersion": scale * (1.0 + y),
                                    "cell": {"row": row, "dial_x": x, "dial_y": y},
                                }
                            )
                        )
        return load_jsonl(out)

    def test_normalising_makes_rows_comparable(self):
        r = self._records()
        fig = plot.surface(r, x="dial_x", y="dial_y", metric="final_dispersion",
                           thresholds=[1.2], baseline_y=0.0)
        arrays = _mesh_values(fig, "dial_x")
        self.assertEqual(len(arrays), 2)
        # Both panels must now show exactly 1.0 at the baseline and 1.5 at y=0.5.
        for a in arrays:
            self.assertEqual(sorted(set(np.round(a, 6))), [1.0, 1.5])

    def test_raw_surface_keeps_the_rows_apart(self):
        r = self._records()
        fig = plot.surface(r, x="dial_x", y="dial_y", metric="final_dispersion")
        arrays = _mesh_values(fig, "dial_x")
        self.assertEqual(len(arrays), 2)
        self.assertNotEqual(sorted(set(np.round(arrays[0], 6))),
                            sorted(set(np.round(arrays[1], 6))))

    def test_unknown_baseline_value_is_an_error(self):
        r = self._records()
        with self.assertRaises(ValueError) as ctx:
            plot.surface(r, x="dial_x", y="dial_y", metric="final_dispersion", baseline_y=0.7)
        self.assertIn("dial_y", str(ctx.exception))


class TestPairedPanels(unittest.TestCase):
    def _records(self):
        import json as _json

        out = []
        for row, prov in (("A", "enumerated"), ("B", "optimiser_found")):
            for lam in (0.05, 0.1):
                for tm in (0.0, 0.5):
                    for i in range(6):
                        out.append(_json.dumps({
                            "minimum_is_tight": prov == "enumerated",
                            "provenance": prov,
                            "ever_single_cluster": tm == 0.0,
                            "final_dispersion": 1.4 * (1.0 + tm),
                            "n": 20, "duration": 600.0,
                            "cell": {"row": row, "terrain.correlation_length": lam,
                                     "terrain.friction_amplitude": tm},
                        }))
        return load_jsonl(out)

    def test_grid_shape_and_normalisation(self):
        r = self._records()
        fig = plot.paired_panels(
            r,
            x="terrain.friction_amplitude",
            metrics=[("ever_single_cluster", "reach", None, "proportion"),
                     ("final_dispersion", "hold", 0.0)],
            col_field="terrain.correlation_length",
        )
        # Only the outer panels carry axis labels, so count by content.
        panels = [a for a in fig.axes if a.get_lines()]
        self.assertEqual(len(panels), 4)  # 2 metrics x 2 lambda columns
        for ax in panels:
            self.assertEqual(len(ax.get_lines()), 2)  # one line per capability row
        # The hold panels are normalised, so every line starts at exactly 1.0.
        hold = [a for a in fig.axes if a.get_ylabel() == "hold"]
        for ax in hold:
            for line in ax.get_lines():
                self.assertAlmostEqual(line.get_ydata()[0], 1.0, places=9)

    def test_rows_keep_their_provenance_markers(self):
        r = self._records()
        fig = plot.paired_panels(
            r,
            x="terrain.friction_amplitude",
            metrics=[("final_dispersion", "hold", 0.0)],
            col_field="terrain.correlation_length",
        )
        labels = [t.get_text() for t in fig.legends[0].get_texts()]
        self.assertTrue(any(l.endswith("†") for l in labels))
        self.assertTrue(any(not l.endswith("†") and not l.endswith("‡") for l in labels))


if __name__ == "__main__":
    unittest.main()


class TestPursuerRangeNormalisation(unittest.TestCase):
    """r_p in metres is not interpretable on its own.

    A pursuer that sees 1.0 m around a swarm started inside 0.74 m sees the
    whole swarm from anywhere in it — that is the degenerate corner of the grid,
    not the hard end of a difficulty axis. Every figure with r_p on an axis has
    to say so, or a reader will read the corner backwards.
    """

    def _rows(self, start_radius=0.74, ranges=(0.1, 0.35, 1.0)):
        import json as _json

        return [
            _json.dumps({
                "minimum_is_tight": True, "provenance": "enumerated",
                "survival_fraction": 1.0 - rp, "start_radius": start_radius,
                "n": 20,
                "cell": {"row": "B0", "pursuer.range": rp, "pursuer.confusion": k},
            })
            for rp in ranges
            for k in (0.0, 1.0)
            for _ in range(3)
        ]

    def test_curve_ticks_carry_start_radius_multiples(self):
        r = load_jsonl(self._rows())
        fig = plot.curve(r, x="pursuer.range", metric="survival_fraction")
        ax = fig.axes[0]
        labels = [t.get_text() for t in ax.get_xticklabels()]
        self.assertIn("0.35\n0.47", labels)
        self.assertIn("1\n1.35", labels)
        self.assertIn("start radii", ax.get_xlabel())
        self.assertTrue(any("perfect-perception" in t.get_text() for t in fig.texts))

    def test_the_perfect_perception_corner_is_marked(self):
        r = load_jsonl(self._rows())
        fig = plot.curve(r, x="pursuer.range", metric="survival_fraction")
        ax = fig.axes[0]
        # The boundary is drawn at the start radius itself...
        boundary = [ln for ln in ax.get_lines()
                    if len(set(ln.get_xdata())) == 1 and ln.get_xdata()[0] == 0.74]
        self.assertEqual(len(boundary), 1)
        # ...and only the ticks past it are called out.
        marked = {t.get_text().split("\n")[0]
                  for t in ax.get_xticklabels() if t.get_color() == "#8a3b00"}
        self.assertEqual(marked, {"1"})

    def test_no_corner_no_marked_ticks(self):
        # Every r_p below the start radius: nothing to call out, but the axis is
        # still labelled in start radii.
        r = load_jsonl(self._rows(ranges=(0.1, 0.2, 0.35)))
        fig = plot.curve(r, x="pursuer.range", metric="survival_fraction")
        ax = fig.axes[0]
        self.assertEqual(
            [t for t in ax.get_xticklabels() if t.get_color() == "#8a3b00"], []
        )
        self.assertIn("start radii", ax.get_xlabel())

    def test_a_swept_start_radius_is_left_alone(self):
        # Normalising by "the" start radius is only meaningful when there is one.
        r = load_jsonl(self._rows(start_radius=0.74) + self._rows(start_radius=1.5))
        fig = plot.curve(r, x="pursuer.range", metric="survival_fraction")
        self.assertEqual(fig.axes[0].get_xlabel(), "pursuer.range")

    def test_surface_marks_the_corner_on_the_r_p_axis(self):
        r = load_jsonl(self._rows())
        fig = plot.surface(r, x="pursuer.range", y="pursuer.confusion",
                           metric="survival_fraction", thresholds=[0.5])
        panels = [a for a in fig.axes if "pursuer.range" in a.get_xlabel()]
        self.assertEqual(len(panels), 1)
        self.assertIn("start radii", panels[0].get_xlabel())
        self.assertTrue(any("perfect-perception" in t.get_text() for t in fig.texts))
