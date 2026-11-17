"""Standard-library tests for the public state-artifact example."""
import hashlib
import json
import unittest
from V3.examples.snapshot_integrity import make_artifact, verify_artifact


class SnapshotIntegrityTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(verify_artifact(make_artifact({"cap": 8, "rounds": 3})), {"cap": 8, "rounds": 3})

    def test_deterministic(self):
        self.assertEqual(make_artifact({"cap": 8, "rounds": 3}), make_artifact({"rounds": 3, "cap": 8}))

    def test_tampered_payload_rejected(self):
        raw = make_artifact({"cap": 8})
        self.assertRaises(ValueError, verify_artifact, raw.replace(b'"cap":8', b'"cap":9'))

    def test_corruption_rejected(self):
        self.assertRaises(ValueError, verify_artifact, make_artifact({"cap": 8})[:-2])

    def test_unsupported_version_rejected_even_when_rehashed(self):
        envelope = json.loads(make_artifact({"cap": 8}))
        envelope["payload"]["version"] = 2
        payload = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        envelope["sha256"] = hashlib.sha256(payload).hexdigest()
        raw = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertRaises(ValueError, verify_artifact, raw)

    def test_untrusted_dev_only(self):
        envelope = json.loads(make_artifact({"cap": 8}))
        envelope["payload"]["trust"] = "TRUSTED"
        payload = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        envelope["sha256"] = hashlib.sha256(payload).hexdigest()
        raw = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertRaises(ValueError, verify_artifact, raw)

    def test_noncanonical_rejected(self):
        self.assertRaises(ValueError, verify_artifact, make_artifact({"cap": 8}) + b' ')

    def test_invalid_state_rejected(self):
        self.assertRaises(ValueError, make_artifact, {"cap": True})

    def test_duplicate_keys_rejected(self):
        self.assertRaises(ValueError, verify_artifact, b'{"payload":{},"payload":{},"sha256":"no"}')


if __name__ == "__main__":
    unittest.main()
