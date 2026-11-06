"""Tests for the standalone public readiness illustration."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "examples" / "unified_readiness_demo.py"
spec = importlib.util.spec_from_file_location("unified_readiness_demo", path)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ReadinessTests(unittest.TestCase):
    def test_ready(self):
        self.assertEqual(module.evaluate_readiness(dict.fromkeys(
            ("operational", "cognitive", "authorization", "recovery"), True)).state, "READY")

    def test_missing_check_fails_closed(self):
        result = module.evaluate_readiness({"operational": True})
        self.assertEqual(result.state, "NOT_READY")
        self.assertIn("authorization:NOT_VERIFIED", result.reasons)

    def test_failed_check(self):
        result = module.evaluate_readiness({"operational": True, "cognitive": True,
             "authorization": False, "recovery": True})
        self.assertEqual(result.reasons, ("authorization:FAILED",))

    def test_non_boolean_fails_closed(self):
        result = module.evaluate_readiness({"operational": 1, "cognitive": True,
             "authorization": True, "recovery": True})
        self.assertEqual(result.state, "NOT_READY")

    def test_unknown_check_rejected(self):
        with self.assertRaises(ValueError):
            module.evaluate_readiness({"unknown": True})


if __name__ == "__main__":
    unittest.main()
