import unittest
from V3.public_core.canonical import canonical_bytes, digest, strict_loads, CanonicalError
from V3.public_core.errors import SkyError
from V3.public_core.units import conform

class PublicCoreTests(unittest.TestCase):
    def test_canonical_key_order(self):
        self.assertEqual(canonical_bytes({"z": 2, "a": 1}), b'{"a":1,"z":2}')
    def test_digest_stability(self):
        self.assertEqual(digest({"a":1}), digest({"a":1}))
    def test_float_rejected(self):
        with self.assertRaises(CanonicalError): canonical_bytes({"v": 1.5})
    def test_duplicate_key_rejected(self):
        with self.assertRaises(SkyError): strict_loads(b'{"a":1,"a":2}')
    def test_invalid_utf8_rejected(self):
        with self.assertRaises(SkyError): strict_loads(b'\xff')
    def test_unit_upscale(self):
        result, audit = conform({"unit":"ms","scale":0,"value":2},"ms",2,"exact_upscale","$.x",1000)
        self.assertEqual(result["value"], 200)
        self.assertEqual(audit["factor"], 100)
    def test_unit_mismatch(self):
        with self.assertRaises(SkyError): conform({"unit":"ms","scale":0,"value":2},"s",0,"none","$.x",1000)
    def test_unit_overflow(self):
        with self.assertRaises(SkyError): conform({"unit":"ms","scale":0,"value":20},"ms",3,"exact_upscale","$.x",1000)

if __name__ == "__main__": unittest.main()
