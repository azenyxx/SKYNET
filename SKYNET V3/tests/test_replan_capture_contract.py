"""Synthetic, standalone tests of the public capture-evidence contract."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "examples" / "replan_capture_contract.py"
SPEC = importlib.util.spec_from_file_location("public_replan_capture_contract", FILE)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class CaptureContractTests(unittest.TestCase):
    def test_matching_state_is_eligible(self):
        self.assertEqual(MOD.comparison_eligible("FEASIBLE", {"A": ["d1"], "B": ["d1"]}, {"A": True, "B": False}), (True, "ELIGIBLE"))

    def test_infeasible_not_eligible(self):
        self.assertFalse(MOD.comparison_eligible("INFEASIBLE", {"A": ["d1"]}, {"A": True})[0])

    def test_unknown_not_eligible(self):
        self.assertFalse(MOD.comparison_eligible("UNKNOWN", {"A": ["d1"]}, {"A": True})[0])

    def test_invalid_not_eligible(self):
        self.assertFalse(MOD.comparison_eligible("INVALID", {"A": ["d1"]}, {"A": True})[0])

    def test_missing_bound_capture_rejected(self):
        self.assertEqual(MOD.comparison_eligible("FEASIBLE", {"A": ["d1"], "B": []}, {"A": True, "B": True})[1], "MISSING_OR_AMBIGUOUS_STATE")

    def test_duplicate_capture_rejected(self):
        self.assertFalse(MOD.comparison_eligible("FEASIBLE", {"A": ["d1", "d1"]}, {"A": True})[0])

    def test_mismatched_state_rejected(self):
        self.assertEqual(MOD.comparison_eligible("FEASIBLE", {"A": ["d1"], "B": ["d2"]}, {"A": True, "B": True})[1], "STATE_MISMATCH")

    def test_policy_set_mismatch_rejected(self):
        self.assertFalse(MOD.comparison_eligible("FEASIBLE", {"A": ["d1"]}, {"B": True})[0])

    def test_non_bool_outcome_rejected(self):
        self.assertEqual(MOD.comparison_eligible("FEASIBLE", {"A": ["d1"]}, {"A": 1})[1], "INVALID_OUTCOME")

    def test_empty_capture_set_rejected(self):
        self.assertFalse(MOD.comparison_eligible("FEASIBLE", {}, {})[0])

    def test_unknown_feasibility_raises(self):
        with self.assertRaises(ValueError): MOD.comparison_eligible("UNKNOWN_VALUE", {"A": ["d1"]}, {"A": True})

    def test_string_not_valid_capture_sequence(self):
        self.assertFalse(MOD.comparison_eligible("FEASIBLE", {"A": "d1"}, {"A": True})[0])


if __name__ == "__main__":
    unittest.main()
