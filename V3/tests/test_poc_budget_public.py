"""Tests for standalone public planning example."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from poc_budget_public import SCENARIOS, BudgetItem, Scenario, verify


class PublicBudgetTests(unittest.TestCase):
    def test_lean(self):
        self.assertEqual(verify(SCENARIOS["lean"]), dict(research=84_000, infrastructure=18_000, reviews_reserve=38_000))

    def test_base(self):
        self.assertEqual(verify(SCENARIOS["base"]), dict(research=200_000, infrastructure=40_000, reviews_reserve=80_000))

    def test_extended(self):
        self.assertEqual(verify(SCENARIOS["extended"]), dict(research=336_000, infrastructure=85_000, reviews_reserve=129_000))

    def test_targets_are_distinct(self):
        self.assertEqual({k: v.target_usd for k,v in SCENARIOS.items()}, dict(lean=140_000, base=320_000, extended=550_000))

    def test_wrong_sum(self):
        with self.assertRaisesRegex(ValueError, "reconcile"):
            verify(replace(SCENARIOS["base"], target_usd=319_999))

    def test_duplicate_items(self):
        a = SCENARIOS["lean"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify(replace(a, items=a.items + (a.items[0],)))

    def test_negative_cost(self):
        a = SCENARIOS["lean"]
        with self.assertRaisesRegex(ValueError, "expense"):
            verify(replace(a, items=(replace(a.items[0], usd=-1),) + a.items[1:]))

    def test_unknown_category(self):
        a = SCENARIOS["lean"]
        with self.assertRaisesRegex(ValueError, "expense"):
            verify(replace(a, items=(replace(a.items[0], category="private"),) + a.items[1:]))

    def test_float_rejected(self):
        a = SCENARIOS["lean"]
        with self.assertRaisesRegex(ValueError, "expense"):
            verify(replace(a, items=(replace(a.items[0], usd=36_000.0),) + a.items[1:]))

    def test_boolean_rejected(self):
        a = SCENARIOS["lean"]
        with self.assertRaisesRegex(ValueError, "expense"):
            verify(replace(a, items=(replace(a.items[0], usd=True),) + a.items[1:]))

    def test_empty_scenario_rejected(self):
        with self.assertRaises(ValueError):
            verify(Scenario("Empty", 1, 1, ()))

    def test_zero_months_rejected(self):
        with self.assertRaises(ValueError):
            verify(replace(SCENARIOS["lean"], months=0))


if __name__ == "__main__":
    unittest.main()
