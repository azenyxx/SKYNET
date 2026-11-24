"""G1 fidelity harness (E-10, M14.F metrics). Deterministic comparison of M2 CNL parses against frozen gold.

Gold = SKYSPEC v1 documents (formal channel) hand-authored from the CNL-001 §6 expected assertions, plus expected
status/codes for non-OK vectors. Comparison is typed and canonical: both sides are validated by M1 and compiled by M3
(CNL via the lineage-preserving compile_cnl adapter); a constraint key is canonical {kind, normalized IR body}
(identifiers kept, source spans excluded), counted as a multiset: TP = |gold ∩ parsed|, FP = |parsed - gold|,
FN = |gold - parsed|. Exact match additionally requires identical typed variables and objective.
Rates are integer rationals {num, den, permille}; a zero denominator is reported as defined=false, permille=null
(never 0 or 1). This is a development harness on CNL-001 vectors, NOT the VA-authored G1 gate campaign; it claims
no independent verification."""
import json
from collections import Counter
from pathlib import Path

from .canonical import canonical_bytes, digest
from .m1_ingest_formal import ingest
from .m2_cnl import compile_cnl, parse_cnl
from .m3_ir import compile_ir

G1_VERSION = "e10.g1.1"


def rate(num, den):
    return {"defined": den > 0, "den": den, "num": num, "permille": (num * 1000) // den if den else None}


def _keys(ir):
    return Counter(canonical_bytes({"body": c["body"], "kind": c["kind"]}).decode() for c in ir["constraints"])


def _vars(ir):
    return [{k: v[k] for k in ("domain", "id", "scale", "type", "unit")} for v in ir["vars"]]


def evaluate_fixture(source, gold):
    r = parse_cnl(source)
    st, est = r["status"], gold["expected_status"]
    codes = sorted({a["code"] for a in r.get("ambiguity", [])}) or ([r["error"]["code"]] if "error" in r else [])
    row = {"actual_codes": codes, "actual_status": st, "expected_codes": sorted(gold.get("expected_codes", [])),
           "expected_status": est, "fixture": gold["fixture"], "fn": 0, "fp": 0, "tp": 0, "exact_match": None,
           "ambiguity_detected": None, "unsupported_rejected": None, "false_acceptance": est != "OK" and st == "OK",
           "false_ambiguity": est == "OK" and st == "AWAITING_INFORMATION"}
    got = _keys(compile_cnl(r)) if st == "OK" else Counter()
    if est == "OK":
        gir = compile_ir(ingest(canonical_bytes(gold["gold_skyspec"])))
        want = _keys(gir)
        row.update(tp=sum((want & got).values()), fp=sum((got - want).values()), fn=sum((want - got).values()))
        row["exact_match"] = st == "OK" and row["fp"] == 0 and row["fn"] == 0 and \
            _vars(compile_cnl(r)) == _vars(gir) and compile_cnl(r)["objective"] == gir["objective"]
    else:
        row["fp"] = sum(got.values())
        if est == "AWAITING_INFORMATION":
            row["ambiguity_detected"] = st == est and codes == row["expected_codes"]
        if est == "ABSTAINED_UNSUPPORTED":
            row["unsupported_rejected"] = st == est
    return row


def evaluate(cases):
    rows = sorted((evaluate_fixture(src, g) for src, g in cases), key=lambda x: x["fixture"])
    tp, fp, fn = (sum(r[k] for r in rows) for k in ("tp", "fp", "fn"))
    ok = [r for r in rows if r["expected_status"] == "OK"]
    aw = [r for r in rows if r["expected_status"] == "AWAITING_INFORMATION"]
    un = [r for r in rows if r["expected_status"] == "ABSTAINED_UNSUPPORTED"]
    rep = {"aggregate": {"ambiguity_detection": rate(sum(r["ambiguity_detected"] for r in aw), len(aw)),
                         "constraint_precision": rate(tp, tp + fp), "constraint_recall": rate(tp, tp + fn),
                         "counts": {"fn": fn, "fp": fp, "tp": tp},
                         "exact_match_rate": rate(sum(bool(r["exact_match"]) for r in ok), len(ok)),
                         "false_acceptance_count": sum(r["false_acceptance"] for r in rows),
                         "false_ambiguity_count": sum(r["false_ambiguity"] for r in rows),
                         "unsupported_rejection": rate(sum(r["unsupported_rejected"] for r in un), len(un))},
           "fixtures": rows, "g1_version": G1_VERSION,
           "scope": "development fixtures from CNL-001 §6 vectors; not the VA-authored G1 gate campaign; no independent verification"}
    rep["report_digest"] = digest(rep)
    return rep


def load_cases(gold_dir, root):
    cases = []
    for p in sorted(Path(gold_dir).glob("*.gold.json")):
        g = json.loads(p.read_text())
        cases.append(((Path(root) / g["source"]).read_bytes(), g))
    return cases
