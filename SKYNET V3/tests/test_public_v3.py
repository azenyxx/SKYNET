"""Public tests for the selected SKYNET V3 foundation utilities."""
import unittest
from skynet_v3.canonical import CanonicalError, canonical_bytes, digest, strict_loads, json_depth
from skynet_v3.errors import SkyError
from skynet_v3.units import conform


class CanonicalTests(unittest.TestCase):
    def test_stable_order_and_unicode(self):
        self.assertEqual(canonical_bytes({"b": 1, "a": [2, "é", None, True]}),
                         b'{"a":[2,"\xc3\xa9",null,true],"b":1}')

    def test_digest_is_order_independent(self):
        self.assertEqual(digest({"z": 4, "a": 2}), digest({"a": 2, "z": 4}))
        self.assertTrue(digest({"a": 1}).startswith("sha256:"))

    def test_reject_float(self):
        with self.assertRaises(CanonicalError):
            canonical_bytes({"x": 1.5})

    def test_reject_non_nfc(self):
        with self.assertRaises(CanonicalError):
            canonical_bytes({"x": "e\u0301"})

    def test_reject_unsupported_type(self):
        with self.assertRaises(CanonicalError):
            canonical_bytes({"x": {1, 2}})

    def test_duplicate_keys(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads(b'{"a":1,"a":2}')
        self.assertEqual(cm.exception.code, "DUPLICATE_KEY")

    def test_invalid_utf8(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads(b"\xff")
        self.assertEqual(cm.exception.code, "INVALID_UTF8")

    def test_nonfinite_number(self):
        with self.assertRaises(SkyError) as cm:
            strict_loads(b'{"x":NaN}')
        self.assertEqual(cm.exception.code, "NON_FINITE_NUMBER")

    def test_nested_input_limit(self):
        raw = ("[" * 33 + "0" + "]" * 33).encode()
        with self.assertRaises(SkyError) as cm:
            strict_loads(raw)
        self.assertEqual(cm.exception.code, "NESTING_TOO_DEEP")

    def test_depth_scanner_ignores_string_brackets(self):
        self.assertEqual(json_depth('{"x":"[[["}'), 1)


class UnitTests(unittest.TestCase):
    def test_exact_upscale(self):
        out, audit = conform({"unit":"ms", "scale":1,"value":12},
                             "ms",3,"exact_upscale","$.duration",100000)
        self.assertEqual(out, {"unit":"ms","scale":3,"value":1200})
        self.assertEqual(audit["factor"],100)

    def test_matching_scale_no_conversion(self):
        out, audit = conform({"unit":"m", "scale":2,"value":7},
                             "m",2,"none","$.x",1000)
        self.assertEqual(out["value"],7)
        self.assertIsNone(audit)

    def test_cross_unit_rejected(self):
        with self.assertRaises(SkyError) as cm:
            conform({"unit":"m","scale":0,"value":1}, "s",0,"none","$.x",100)
        self.assertEqual(cm.exception.code,"UNIT_MISMATCH")

    def test_downscale_rejected(self):
        with self.assertRaises(SkyError) as cm:
            conform({"unit":"m","scale":3,"value":1000}, "m",2,"exact_upscale","$.x",10000)
        self.assertEqual(cm.exception.code,"UNIT_MISMATCH")

    def test_overflow_rejected(self):
        with self.assertRaises(SkyError) as cm:
            conform({"unit":"m","scale":0,"value":100}, "m",3,"exact_upscale","$.x",999)
        self.assertEqual(cm.exception.code,"RESCALE_OVERFLOW")


if __name__ == "__main__":
    unittest.main()
