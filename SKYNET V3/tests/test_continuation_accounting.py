"""Unit tests for standalone public examples; no private test fixtures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from continuation_accounting import TaskObservation, summarize


class TestAccounting(unittest.TestCase):
    def test_empty_is_not_evaluable(self):
        self.assertEqual(summarize([])["verdict"], "NOT_EVALUABLE")

    def test_feasible_with_matching_state_is_eligible(self):
        result = summarize([TaskObservation("a", "feasible", True, (True, False))])
        self.assertEqual((result["repair_eligible"], result["method_sensitive"]), (1, 1))

    def test_equal_outcomes_not_sensitive(self):
        result = summarize([TaskObservation("a", "feasible", True, (True, True))])
        self.assertEqual(result["method_sensitive"], 0)

    def test_no_state_match_is_not_eligible(self):
        result = summarize([TaskObservation("a", "feasible", False, (True, False))])
        self.assertEqual(result["repair_eligible"], 0)

    def test_missing_outcomes_is_not_eligible(self):
        result = summarize([TaskObservation("a", "feasible", True, ())])
        self.assertEqual(result["repair_eligible"], 0)

    def test_infeasible_is_not_eligible(self):
        result = summarize([TaskObservation("a", "infeasible", True, (True, False))])
        self.assertEqual(result["repair_eligible"], 0)

    def test_unknown_is_not_eligible(self):
        result = summarize([TaskObservation("a", "unknown", True, (True, False))])
        self.assertEqual(result["repair_eligible"], 0)

    def test_counts_include_invalid_and_no_replan(self):
        data = [TaskObservation("a", "invalid"), TaskObservation("b", "no_replan")]
        counts = summarize(data)["by_feasibility"]
        self.assertEqual((counts["invalid"], counts["no_replan"]), (1, 1))

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            summarize([TaskObservation("a", "feasible"), TaskObservation("a", "invalid")])

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValueError):
            summarize([TaskObservation("a", "maybe")])

    def test_nonboolean_outcome_rejected(self):
        with self.assertRaises(TypeError):
            summarize([TaskObservation("a", "feasible", True, (1, False))])

    def test_nonboolean_state_rejected(self):
        with self.assertRaises(TypeError):
            summarize([TaskObservation("a", "feasible", 1, (True, False))])

    def test_multiple_cases(self):
        rows = [TaskObservation("a", "feasible", True, (False, True)),
                TaskObservation("b", "feasible", True, (True, True)),
                TaskObservation("c", "infeasible")]
        self.assertEqual((summarize(rows)["total"], summarize(rows)["method_sensitive"]), (3, 1))


if __name__ == "__main__":
    unittest.main()
