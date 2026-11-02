"""Tests for the public educational illustration."""
import unittest
from shift_demo import choose_route, realized_cost


class ShiftDemoTests(unittest.TestCase):
    def test_high_hazard_selects_detour(self):
        self.assertEqual(choose_route(0.8), "detour")

    def test_low_hazard_selects_direct(self):
        self.assertEqual(choose_route(0.1), "direct")

    def test_negative_transfer_under_shift(self):
        self.assertGreater(realized_cost("detour", False), realized_cost("direct", False))

    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            choose_route(1.2)


if __name__ == "__main__":
    unittest.main()
