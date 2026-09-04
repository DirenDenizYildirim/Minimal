import json
import unittest

from swarm_harness.load import load_jsonl


def record(**over):
    base = {
        "run_index": 0,
        "seed": 1,
        "n": 20,
        "duration": 600.0,
        "capability": {
            "sensor_states": 2,
            "memory_bits": 0,
            "arithmetic": False,
            "comm_bits": 0,
        },
        "provenance": "enumerated",
        "minimum_is_tight": True,
        "final_dispersion": 1.4,
        "final_largest_cluster_fraction": 1.0,
        "cell": {"sweep": "s", "row": "M0", "occlusion.fn_rate": 0.1},
    }
    base.update(over)
    return json.dumps(base)


class TestLoad(unittest.TestCase):
    def test_cell_and_capability_are_flattened(self):
        r = load_jsonl([record()])
        self.assertEqual(len(r), 1)
        self.assertEqual(r.column("occlusion.fn_rate"), [0.1])
        self.assertEqual(r.column("row"), ["M0"])
        self.assertEqual(r.column("capability.S"), [2])
        self.assertEqual(r.column("capability"), ["(2,0,0,0)"])

    def test_group_and_filter(self):
        rows = [
            record(cell={"row": "M0", "occlusion.fn_rate": 0.1}),
            record(cell={"row": "M0", "occlusion.fn_rate": 0.2}),
            record(cell={"row": "M1", "occlusion.fn_rate": 0.1}),
        ]
        r = load_jsonl(rows)
        self.assertEqual(sorted(r.unique("row")), ["M0", "M1"])
        self.assertEqual(len(r.group_by(["row"])), 2)
        self.assertEqual(len(r.filter(row="M0")), 2)
        self.assertEqual(len(r.group_by(["row", "occlusion.fn_rate"])), 3)

    def test_upper_bound_rows_are_detected(self):
        tight = record(cell={"row": "M0"}, minimum_is_tight=True)
        loose = record(cell={"row": "M1"}, minimum_is_tight=False, provenance="optimiser_found")
        self.assertFalse(load_jsonl([tight]).any_upper_bound())
        both = load_jsonl([tight, loose])
        self.assertTrue(both.any_upper_bound())
        self.assertEqual(both.upper_bound_rows(), ["M1"])
        # A row without the flag must not be silently treated as an upper bound.
        self.assertFalse(load_jsonl([tight]).upper_bound_rows())

    def test_missing_field_names_what_is_available(self):
        r = load_jsonl([record()])
        with self.assertRaises(KeyError) as ctx:
            r.column("nope")
        self.assertIn("final_dispersion", str(ctx.exception))

    def test_empty_input_is_an_error(self):
        with self.assertRaises(ValueError):
            load_jsonl([])
        with self.assertRaises(ValueError):
            load_jsonl(["", "  "])


if __name__ == "__main__":
    unittest.main()
