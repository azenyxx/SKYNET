"""Public subset smoke tests; no private SKYNET runtime required."""
import hashlib
import io
import pathlib
import sys
import tempfile
import unittest
import zipfile
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from skynet_v2_eval.prng import DetRNG
from skynet_v2_eval.stats import q6_round, wilson_q6
from skynet_v2_trust.ids import new_id, id_from_text
from skynet_v2_trust.errors import TrustError
from verify_release import inspect_archive


class PublicSubsetTests(unittest.TestCase):
    def test_deterministic_prng(self):
        a, b = DetRNG(b"test", "public"), DetRNG(b"test", "public")
        self.assertEqual([a.below(1000) for _ in range(50)], [b.below(1000) for _ in range(50)])

    def test_ulid_identifiers(self):
        self.assertEqual(len(new_id()), 26)
        self.assertEqual(id_from_text("same"), id_from_text("same"))
        self.assertNotEqual(id_from_text("same"), id_from_text("different"))

    def test_fail_closed_error(self):
        error = TrustError("E-AUTH-001", "denied")
        self.assertEqual(error.policy, "FAIL_CLOSED")
        self.assertEqual(error.code, "E-AUTH-001")

    def test_q6_rounding(self):
        self.assertEqual(q6_round(Fraction(5, 2)), 2)
        self.assertEqual(q6_round(Fraction(7, 2)), 4)

    def test_wilson_interval(self):
        result = wilson_q6(7, 10, 950000)
        self.assertIsInstance(result, dict)

    def test_archive_verifier(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "example.zip"
            data = b"public example"
            digest = hashlib.sha256(data).hexdigest()
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("release/data.bin", data)
                z.writestr("release/MANIFEST.sha256", f"{digest}  data.bin\n")
            self.assertTrue(inspect_archive(path)["ok"])
            self.assertFalse(inspect_archive(path, "0" * 64)["ok"])

    def test_archive_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "example.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("release/data.bin", b"tampered")
                z.writestr("release/MANIFEST.sha256", hashlib.sha256(b"original").hexdigest() + "  data.bin\n")
            self.assertFalse(inspect_archive(path)["ok"])


if __name__ == "__main__":
    unittest.main()
