"""T-SER golden serialization vectors (tests/golden/t_ser_vectors.json)."""
import json
import unittest

from skynet_v3.canonical import canonical_bytes, digest
from skynet_v3.errors import SkyError
from skynet_v3.m1_ingest_formal import ingest
from skynet_v3.m3_ir import compile_ir
from tests._ref import FIX, NAMES, ROOT

G = json.loads((ROOT / "tests" / "golden" / "t_ser_vectors.json").read_text())


class TSerTests(unittest.TestCase):
    def test_canonical_vectors(self):
        for v in G["canonical"]:
            with self.subTest(v["name"]):
                self.assertEqual(canonical_bytes(v["obj"]), v["expected"].encode("utf-8"))
                self.assertEqual(digest(v["obj"]), v["digest"])

    def test_accept_vectors_stable_digests(self):
        for v in G["ingest_accept"]:
            with self.subTest(v["name"]):
                spec = ingest(v["raw"].encode("utf-8"))
                self.assertEqual(spec["spec_digest"], v["spec_digest"])
                self.assertEqual(compile_ir(spec)["ir_digest"], v["ir_digest"])

    def test_constraint_order_normalized(self):
        """Source order changes spec digest and byte-level source spans (traceability), but the
        normalized constraint list (sorted by cid, identical bodies) must not depend on source order."""
        a = {v["name"]: v for v in G["ingest_accept"]}
        self.assertNotEqual(a["constraint_order_a"]["spec_digest"], a["constraint_order_b"]["spec_digest"])
        irs = [compile_ir(ingest(a[n]["raw"].encode("utf-8"))) for n in ("constraint_order_a", "constraint_order_b")]
        strip = lambda ir: [(c["cid"], c["kind"], c["body"]) for c in ir["constraints"]]  # noqa: E731
        self.assertEqual(strip(irs[0]), strip(irs[1]))
        self.assertEqual([c["cid"] for c in irs[0]["constraints"]], ["c1", "c2"])
        self.assertEqual(irs[0]["vars"], irs[1]["vars"])

    def test_reject_vectors(self):
        for v in G["ingest_reject"]:
            with self.subTest(v["name"]):
                with self.assertRaises(SkyError) as cm:
                    ingest(v["raw"].encode("utf-8"))
                self.assertEqual(cm.exception.code, v["code"])

    def test_fixture_spec_and_ir_digests_golden(self):
        exp = json.loads((FIX / "EXPECTED_E02.json").read_text())["fixtures"]
        for n in NAMES:
            spec = ingest((FIX / f"{n}.json").read_bytes())
            self.assertEqual(spec["spec_digest"], exp[n]["spec_digest"], n)
            self.assertEqual(compile_ir(spec)["ir_digest"], exp[n]["ir_digest"], n)


if __name__ == "__main__":
    unittest.main()
