import json
import unittest

from swarm_harness.load import load_jsonl
from swarm_harness import plot


def cells(rows, xs, ys, tight=True):
    out = []
    for row in rows:
        for x in xs:
            for y in ys:
                for i in range(5):
                    out.append(
                        json.dumps(
                            {
                                "minimum_is_tight": tight,
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

    def test_upper_bound_rows_are_stamped(self):
        r = load_jsonl(cells(["M1"], [0.0, 0.2], [20], tight=False))
        fig = plot.curve(r, x="occlusion.fn_rate", metric="final_largest_cluster_fraction")
        labels = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertTrue(any("†" in l for l in labels))
        self.assertTrue(any("UPPER BOUND" in t.get_text() for t in fig.texts))

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


if __name__ == "__main__":
    unittest.main()
