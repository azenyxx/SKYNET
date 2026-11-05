"""Tests for the standalone public reference example, not private V2 tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from canonical_metrics import canonical_metrics, evidence_digest


class CanonicalMetricsTests(unittest.TestCase):
    def test_repeatable(self):
        m = canonical_metrics(covered=29, total=50, utility_q6=939000)
        self.assertEqual(evidence_digest(m), evidence_digest(dict(reversed(list(m.items())))))

    def test_tampering_changes_digest(self):
        m = canonical_metrics(covered=29, total=50, utility_q6=939000)
        n = canonical_metrics(covered=30, total=50, utility_q6=939000)
        self.assertNotEqual(evidence_digest(m), evidence_digest(n))

    def test_reject_float_and_bool(self):
        for bad in (0.5, True, None, "29"):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    canonical_metrics(covered=bad, total=50, utility_q6=939000)

    def test_reject_invalid_counts(self):
        with self.assertRaises(ValueError):
            canonical_metrics(covered=51, total=50, utility_q6=939000)

    def test_reject_extra_fields(self):
        m = canonical_metrics(covered=29, total=50, utility_q6=939000)
        m["untrusted"] = 1
        with self.assertRaises(ValueError):
            evidence_digest(m)


if __name__ == "__main__":
    unittest.main()
