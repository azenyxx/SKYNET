"""Tests for the public reference evaluator only (not private SKYNET)."""
import unittest
from public_eval import Action, bounded_plan, demo

class ReferenceEvaluatorTests(unittest.TestCase):
    def test_safe_path(self):
        self.assertEqual(demo()["reference_plan"], ["collect_key", "open_door", "enter"])
        self.assertTrue(demo()["safe"])

    def test_unreachable(self):
        self.assertIsNone(bounded_plan(set(), {"missing"}, []))

    def test_depth_bound(self):
        action = Action("step", frozenset(), frozenset({"done"}))
        self.assertIsNone(bounded_plan(set(), {"done"}, [action], max_depth=0))

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            bounded_plan(set(), set(), [], max_states=0)

    def test_forbidden_initial(self):
        self.assertIsNone(bounded_plan({"unsafe"}, {"goal"}, [], forbidden={"unsafe"}))

if __name__ == "__main__":
    unittest.main()
