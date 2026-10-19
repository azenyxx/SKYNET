"""Small, dependency-free smoke test for SKYNET public repository."""

from hashlib import sha256
import json
import unittest


def canonical_digest(payload: dict[str, object]) -> str:
    """Return a stable SHA-256 digest for a JSON-compatible mapping."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


class SmokeTests(unittest.TestCase):
    def test_digest_is_independent_of_key_order(self) -> None:
        self.assertEqual(canonical_digest({"a": 1, "b": 2}), canonical_digest({"b": 2, "a": 1}))

    def test_digest_changes_with_payload(self) -> None:
        self.assertNotEqual(canonical_digest({"stage": "COG-014"}), canonical_digest({"stage": "COG-015"}))

    def test_digest_has_sha256_hex_length(self) -> None:
        self.assertEqual(len(canonical_digest({"project": "SKYNET"})), 64)


if __name__ == "__main__":
    unittest.main()
