"""Tests for the standalone public illustration only."""
import unittest
from orchestration_lifecycle_demo import BoundedLifecycle, State


class LifecycleTests(unittest.TestCase):
    def test_normal_path(self):
        m = BoundedLifecycle()
        self.assertEqual(m.preflight(test_profile=True, snapshot_current=True), State.BOUND)
        m.start()
        m.step()
        self.assertEqual(m.finish(evidence_persisted=True), State.SEALED)

    def test_non_test_profile_refused(self):
        m = BoundedLifecycle()
        self.assertEqual(m.preflight(test_profile=False, snapshot_current=True), State.REFUSED)

    def test_stale_snapshot_refused(self):
        m = BoundedLifecycle()
        self.assertEqual(m.preflight(test_profile=True, snapshot_current=False), State.REFUSED)

    def test_evidence_failure_halts(self):
        m = BoundedLifecycle()
        m.preflight(test_profile=True, snapshot_current=True)
        m.start()
        self.assertEqual(m.finish(evidence_persisted=False), State.HALTED)

    def test_budget_is_bounded(self):
        m = BoundedLifecycle(max_steps=1)
        m.preflight(test_profile=True, snapshot_current=True)
        m.start()
        m.step()
        self.assertEqual(m.step(), State.HALTED)

    def test_terminal_cannot_restart(self):
        m = BoundedLifecycle()
        m.stop()
        self.assertEqual(m.stop(), State.HALTED)
        with self.assertRaises(ValueError):
            m.start()


if __name__ == "__main__":
    unittest.main()
