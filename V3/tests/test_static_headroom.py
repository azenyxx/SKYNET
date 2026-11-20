"""Synthetic tests for a public, standalone research accounting example."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "examples" / "static_headroom.py"
SPEC = importlib.util.spec_from_file_location("public_static_headroom", FILE)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class StaticHeadroomTests(unittest.TestCase):
    def test_no_headroom_when_one_policy_dominates(self):
        r = MOD.static_headroom({"fixed": [True, True, False], "other": [True, False, False]})
        self.assertEqual((r["best_fixed_successes"], r["oracle_successes"], r["headroom_tasks"]), (2, 2, 0))

    def test_complementary_policies_create_headroom(self):
        r = MOD.static_headroom({"one": [True, False], "two": [False, True]})
        self.assertEqual((r["best_fixed_successes"], r["oracle_successes"], r["headroom_tasks"]), (1, 2, 1))

    def test_ties_are_canonical(self):
        r = MOD.static_headroom({"z": [True, False], "a": [False, True]})
        self.assertEqual(r["best_fixed_policies"], ("a", "z"))

    def test_one_policy(self):
        r = MOD.static_headroom({"only": [False, True]})
        self.assertEqual(r["headroom_tasks"], 0)

    def test_all_fail(self):
        r = MOD.static_headroom({"a": [False], "b": [False]})
        self.assertEqual(r["oracle_successes"], 0)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError): MOD.static_headroom({})

    def test_zero_tasks_rejected(self):
        with self.assertRaises(ValueError): MOD.static_headroom({"a": []})

    def test_unequal_length_rejected(self):
        with self.assertRaises(ValueError): MOD.static_headroom({"a": [True], "b": [True, False]})

    def test_truthy_integer_rejected(self):
        with self.assertRaises(ValueError): MOD.static_headroom({"a": [1]})

    def test_invalid_policy_name_rejected(self):
        with self.assertRaises(ValueError): MOD.static_headroom({"": [True]})


if __name__ == "__main__":
    unittest.main()
