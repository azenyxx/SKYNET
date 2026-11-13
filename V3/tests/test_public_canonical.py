"""Public-safe tests for the unmodified canonicalization and typed-error utilities."""
import unittest
from skynet_v3.canonical import canonical_bytes, CanonicalError, strict_loads
from skynet_v3.errors import SkyError

class PublicCanonicalTests(unittest.TestCase):
    def test_sorted_integer_json(self):
        self.assertEqual(canonical_bytes({"z": 1, "a": [True, 2]}), b'{"a":[true,2],"z":1}')
    def test_reject_float(self):
        with self.assertRaises(CanonicalError): canonical_bytes({"score": 1.5})
    def test_reject_tuple(self):
        with self.assertRaises(CanonicalError): canonical_bytes(("fixture", b"raw"))
    def test_duplicate_key(self):
        with self.assertRaises(SkyError): strict_loads(b'{"a":1,"a":2}')
    def test_reject_non_integer(self):
        with self.assertRaises(SkyError): strict_loads(b'{"a":1.5}')

if __name__ == "__main__": unittest.main()
