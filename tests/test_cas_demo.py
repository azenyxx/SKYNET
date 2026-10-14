"""Public tests for the synthetic, non-authoritative CAS example."""
import unittest

from examples.cas_demo.model import Command, Rejected, Snapshot, apply


class CasDemoTests(unittest.TestCase):
    def setUp(self):
        self.initial = Snapshot(0, b"old")

    def test_success_returns_new_immutable_snapshot(self):
        updated, receipt = apply(self.initial, Command("op-1", 0, b"new"))
        self.assertEqual((self.initial.revision, self.initial.value), (0, b"old"))
        self.assertEqual((updated.revision, updated.value), (1, b"new"))
        self.assertEqual(receipt.revision, 1)

    def test_exact_replay_does_not_advance_revision(self):
        updated, receipt = apply(self.initial, Command("op-1", 0, b"new"))
        replayed, replay_receipt = apply(updated, Command("op-1", 0, b"new"))
        self.assertIs(replayed, updated)
        self.assertEqual(replay_receipt, receipt)
        self.assertEqual(len(replayed.receipts), 1)

    def test_changed_payload_replay_rejected(self):
        updated, _ = apply(self.initial, Command("op-1", 0, b"new"))
        with self.assertRaisesRegex(Rejected, "operation conflict"):
            apply(updated, Command("op-1", 0, b"tampered"))

    def test_changed_expected_revision_replay_rejected(self):
        updated, _ = apply(self.initial, Command("op-1", 0, b"new"))
        with self.assertRaisesRegex(Rejected, "operation conflict"):
            apply(updated, Command("op-1", 1, b"new"))

    def test_stale_revision_rejected(self):
        with self.assertRaisesRegex(Rejected, "stale revision"):
            apply(self.initial, Command("op-2", 7, b"new"))

    def test_overflow_rejected(self):
        maximum = Snapshot((1 << 63) - 1, b"old")
        with self.assertRaisesRegex(Rejected, "revision overflow"):
            apply(maximum, Command("op-3", maximum.revision, b"new"))

    def test_empty_operation_rejected(self):
        with self.assertRaisesRegex(Rejected, "invalid operation id"):
            apply(self.initial, Command("", 0, b"new"))

    def test_bad_payload_rejected(self):
        with self.assertRaisesRegex(Rejected, "invalid payload"):
            apply(self.initial, Command("op", 0, "not-bytes"))

    def test_bool_revision_rejected(self):
        with self.assertRaisesRegex(Rejected, "invalid expected revision"):
            apply(self.initial, Command("op", True, b"new"))

    def test_second_operation_preserves_first_receipt(self):
        one, first = apply(self.initial, Command("op-1", 0, b"one"))
        two, second = apply(one, Command("op-2", 1, b"two"))
        self.assertEqual(two.receipts, (first, second))
        replayed, receipt = apply(two, Command("op-1", 0, b"one"))
        self.assertIs(replayed, two)
        self.assertEqual(receipt, first)


if __name__ == "__main__":
    unittest.main()
