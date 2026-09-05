import unittest

import numpy as np

from swarm_harness.stats import (
    bootstrap_ci,
    fraction_meeting,
    median_ci,
    proportion_ci,
    summarise,
    wilson_ci,
)


class TestStats(unittest.TestCase):
    def test_median_ci_brackets_the_median(self):
        rng = np.random.default_rng(1)
        v = rng.normal(5.0, 1.0, size=500)
        med, lo, hi = median_ci(v)
        self.assertLess(lo, med)
        self.assertLess(med, hi)
        self.assertAlmostEqual(med, 5.0, delta=0.2)

    def test_ci_narrows_with_more_runs(self):
        rng = np.random.default_rng(2)
        small = rng.normal(0, 1, size=30)
        large = rng.normal(0, 1, size=3000)
        _, lo_s, hi_s = median_ci(small)
        _, lo_l, hi_l = median_ci(large)
        self.assertLess(hi_l - lo_l, hi_s - lo_s)

    def test_bootstrap_is_deterministic(self):
        v = [1.0, 2.0, 3.0, 4.0, 10.0]
        self.assertEqual(bootstrap_ci(v), bootstrap_ci(v))

    def test_degenerate_inputs(self):
        self.assertEqual(summarise([]).n, 0)
        self.assertTrue(np.isnan(summarise([]).median))
        self.assertEqual(bootstrap_ci([7.0]), (7.0, 7.0))
        # NaNs are dropped, not propagated.
        s = summarise([1.0, float("nan"), 3.0])
        self.assertEqual(s.n, 2)
        self.assertEqual(s.median, 2.0)

    def test_fraction_meeting_respects_direction(self):
        v = [0.2, 0.5, 0.9, 1.0]
        self.assertEqual(fraction_meeting(v, 0.5), 0.75)
        self.assertEqual(fraction_meeting(v, 0.5, higher_is_better=False), 0.5)

    def test_median_is_used_not_mean_on_bimodal_data(self):
        # The case the docstring warns about: a mean lands where no run sits.
        v = [0.0] * 40 + [1.0] * 60
        s = summarise(v)
        self.assertEqual(s.median, 1.0)
        self.assertAlmostEqual(s.mean, 0.6)


    def test_proportion_is_not_the_median_for_a_boolean(self):
        # 86 successes in 100: the median is exactly 1 and says nothing.
        v = [1.0] * 86 + [0.0] * 14
        self.assertEqual(median_ci(v)[0], 1.0)
        p, lo, hi = proportion_ci(v)
        self.assertAlmostEqual(p, 0.86)
        self.assertLess(lo, 0.86)
        self.assertGreater(hi, 0.86)
        self.assertLess(hi, 1.0)

    def test_wilson_stays_finite_at_the_boundaries(self):
        # The reason not to bootstrap a proportion: resampling 100 successes out
        # of 100 gives 100 successes every time, so the bootstrap claims a
        # zero-width interval exactly where the data is weakest.
        ones = [1.0] * 100
        self.assertEqual(bootstrap_ci(ones, statistic=np.mean), (1.0, 1.0))
        p, lo, hi = wilson_ci(ones)
        self.assertEqual(p, 1.0)
        self.assertEqual(hi, 1.0)
        self.assertLess(lo, 1.0)
        self.assertGreater(lo, 0.9)

        p, lo, hi = wilson_ci([0.0] * 100)
        self.assertEqual((p, lo), (0.0, 0.0))
        self.assertGreater(hi, 0.0)
        self.assertLess(hi, 0.1)

    def test_wilson_matches_the_textbook_interval(self):
        # 60 of 100 at 95%: the standard Wilson answer is [0.5020, 0.6906].
        p, lo, hi = wilson_ci([1.0] * 60 + [0.0] * 40)
        self.assertAlmostEqual(p, 0.60)
        self.assertAlmostEqual(lo, 0.5020, places=3)
        self.assertAlmostEqual(hi, 0.6906, places=3)

    def test_wilson_narrows_with_more_samples(self):
        narrow = wilson_ci([1.0] * 600 + [0.0] * 400)
        wide = wilson_ci([1.0] * 6 + [0.0] * 4)
        self.assertLess(narrow[2] - narrow[1], wide[2] - wide[1])

    def test_proportion_handles_degenerate_cases(self):
        self.assertEqual(proportion_ci([1.0] * 10)[0], 1.0)
        self.assertEqual(proportion_ci([0.0] * 10)[0], 0.0)
        self.assertTrue(np.isnan(proportion_ci([])[0]))
        with self.assertRaises(ValueError):
            wilson_ci([1.0, 0.0], confidence=0.42)


if __name__ == "__main__":
    unittest.main()
