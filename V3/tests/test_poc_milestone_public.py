"""Tests for public evidence gate example."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from poc_milestone_public import Check, Verdict, REQUIRED_LOOP_CHECKS, assess

class PublicMilestoneTests(unittest.TestCase):
    def full(self):
        return [Check(k, Verdict.PASS, f"digest-{k}") for k in REQUIRED_LOOP_CHECKS]

    def test_all_evidence_passes(self):
        self.assertEqual(assess(self.full())["status"], "PASS")

    def test_missing_check_not_qualified(self):
        out = assess(self.full()[:-1])
        self.assertEqual(out["status"], "NOT_QUALIFIED")
        self.assertIn("independent_replay", out["missing"])

    def test_failed_check(self):
        rows = self.full()
        rows[0] = Check("plan_valid", Verdict.FAIL)
        self.assertIn("plan_valid", assess(rows)["failed"])

    def test_explicit_missing(self):
        rows = self.full()
        rows[1] = Check("action_authorized", Verdict.MISSING)
        self.assertIn("action_authorized", assess(rows)["missing"])

    def test_no_false_pass_if_missing_and_failed(self):
        self.assertEqual(assess([Check("plan_valid", Verdict.FAIL)])["status"], "NOT_QUALIFIED")

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            assess(self.full() + [self.full()[0]])

    def test_pass_without_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "digest"):
            assess([Check("plan_valid", Verdict.PASS)])

    def test_empty_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "digest"):
            assess([Check("plan_valid", Verdict.PASS, "  ")])

    def test_unknown_extra_does_not_override_missing(self):
        out = assess([Check("other", Verdict.PASS, "digest")])
        self.assertEqual(out["status"], "NOT_QUALIFIED")

    def test_invalid_verdict_rejected(self):
        with self.assertRaisesRegex(ValueError, "verdict"):
            assess([Check("plan_valid", "PASS", "digest")])

    def test_custom_required(self):
        self.assertEqual(assess([Check("x", Verdict.PASS, "a")], ("x",))["status"], "PASS")

    def test_invalid_required(self):
        with self.assertRaisesRegex(ValueError, "required"):
            assess([], ("x", "x"))

    def test_no_unverified_claims(self):
        self.assertEqual(assess([])["status"], "NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()
