"""Regression tests for the additive public V2 evidence utilities."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from skynet_v2_eval.paired_evidence import EvidenceError, evaluate_pairs
from skynet_v2_eval.split_guard import validate_splits


def records():
    return [
        {"task_id": task, "participant": who, "score_q6": score, "cost_units": cost, "status": "VERIFIED"}
        for task, vals in (("t1", (("sky", 800000, 9), ("base", 700000, 10))), ("t2", (("sky", 600000, 8), ("base", 700000, 7))), ("t3", (("sky", 900000, 5), ("base", 900000, 6))))
        for who, score, cost in vals
    ]


class PairedEvidenceTests(unittest.TestCase):
    def test_paired_summary(self):
        out = evaluate_pairs(records(), candidate="sky", baseline="base")
        self.assertEqual((out["pairs"], out["wins"], out["losses"], out["ties"]), (3, 1, 1, 1))
        self.assertEqual(out["mean_score_delta_q6"], 0)
        self.assertEqual((out["candidate_total_cost_units"], out["baseline_total_cost_units"]), (22, 23))
        self.assertEqual(out["qualification"], "NOT_ASSESSED")

    def test_order_independent_fingerprint(self):
        self.assertEqual(evaluate_pairs(records(), candidate="sky", baseline="base"), evaluate_pairs(list(reversed(records())), candidate="sky", baseline="base"))

    def test_missing_pair(self):
        with self.assertRaises(EvidenceError):
            evaluate_pairs(records()[:-1], candidate="sky", baseline="base")

    def test_duplicate(self):
        with self.assertRaises(EvidenceError):
            evaluate_pairs(records() + [records()[0]], candidate="sky", baseline="base")

    def test_unverified(self):
        data = records(); data[0]["status"] = "UNVERIFIED"
        with self.assertRaises(EvidenceError):
            evaluate_pairs(data, candidate="sky", baseline="base")

    def test_invalid_scores_and_cost(self):
        for key, val in (("score_q6", 1000001), ("score_q6", True), ("cost_units", 0), ("cost_units", 1.5)):
            with self.subTest(key=key, val=val):
                data = records(); data[0][key] = val
                with self.assertRaises(EvidenceError):
                    evaluate_pairs(data, candidate="sky", baseline="base")

    def test_invalid_schema(self):
        data = records(); data[0]["unexpected"] = 1
        with self.assertRaises(EvidenceError):
            evaluate_pairs(data, candidate="sky", baseline="base")

    def test_same_participant(self):
        with self.assertRaises(EvidenceError):
            evaluate_pairs(records(), candidate="sky", baseline="sky")

    def test_disjoint_splits(self):
        out = validate_splits(["t2", "t1"], ["v1"], ["h1"])
        self.assertEqual(out["status"], "ID_DISJOINT_ONLY")
        self.assertEqual(out, validate_splits(["t1", "t2"], ["v1"], ["h1"]))

    def test_overlap_rejected(self):
        with self.assertRaises(EvidenceError):
            validate_splits(["t1"], ["v1"], ["t1"])

    def test_duplicate_split_rejected(self):
        with self.assertRaises(EvidenceError):
            validate_splits(["t1", "t1"], ["v1"], ["h1"])

    def test_empty_split_rejected(self):
        with self.assertRaises(EvidenceError):
            validate_splits(["t1"], [], ["h1"])

    def test_invalid_split_input(self):
        for bad in ("string", ["bad id"], [""], [3]):
            with self.subTest(bad=bad):
                with self.assertRaises(EvidenceError):
                    validate_splits(bad, ["v1"], ["h1"])


if __name__ == "__main__":
    unittest.main()
