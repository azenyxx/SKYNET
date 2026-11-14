"""Public smoke tests for the unchanged V3 canonical JSON implementation."""
import unittest
from skynet_v3.canonical import CanonicalError, canonical_bytes, digest, strict_loads
from skynet_v3.errors import SkyError

class PublicCanonicalTests(unittest.TestCase):
    def test_deterministic_key_order(self):
        self.assertEqual(canonical_bytes({"z": 2, "a": 1}), b'{"a":1,"z":2}')

    def test_digest_determinism(self):
        self.assertEqual(digest({"b": 2, "a": 1}), digest({"a": 1, "b": 2}))
        self.assertTrue(digest({"a": 1}).startswith("sha256:"))

    def test_reject_noncanonical_values(self):
        for obj in (1.5, (1, 2), {1: "x"}, "e\u0301"):
            with self.subTest(obj=repr(obj)), self.assertRaises(CanonicalError):
                canonical_bytes(obj)

    def test_reject_duplicate_keys(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads(b'{"a":1,"a":2}')
        self.assertEqual(cm.exception.code, "DUPLICATE_KEY")

    def test_reject_float_and_nonfinite(self):
        for raw in (b'{"x":1.2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(SkyError):
                strict_loads(raw)

    def test_reject_invalid_utf8(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads(b'\xff')
        self.assertEqual(cm.exception.code, "INVALID_UTF8")

    def test_reject_excessive_nesting(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads((b'[' * 33) + b'0' + (b']' * 33))
        self.assertEqual(cm.exception.code, "NESTING_TOO_DEEP")

    def test_roundtrip(self):
        obj={"constraints":[{"kind":"precedence","lag":6}],"version":3}
        self.assertEqual(strict_loads(canonical_bytes(obj)),obj)

if __name__ == "__main__": unittest.main()
