import json
import unittest
from dataclasses import replace
from cognitive_contracts import *
from test_cognitive_runtime import initial,advance,ID
class ContractTests(unittest.TestCase):
    def test_roundtrip(self):
        s=advance(initial(),'VALIDATE'); raw=canonical_bytes(s)
        self.assertEqual(parse_dto(raw,CognitiveStateV1),s); self.assertEqual(raw,canonical_bytes(s))
    def test_unknown(self):
        d=json.loads(canonical_bytes(initial())); d['unknown']=True
        with self.assertRaisesRegex(ContractError,'FIELDS'): parse_dto(json.dumps(d).encode(),CognitiveStateV1)
    def test_missing(self):
        d=json.loads(canonical_bytes(initial())); del d['task']
        with self.assertRaises(ContractError): parse_dto(json.dumps(d).encode(),CognitiveStateV1)
    def test_duplicate(self):
        with self.assertRaisesRegex(ContractError,'DUPLICATE_KEY'): parse_dto(b'{"x":1,"x":2}',CognitiveTaskV1)
    def test_negative(self):
        with self.assertRaises(ContractError): ResourcesV1(-1,0,0,0,0)
    def test_bool(self):
        with self.assertRaises(ContractError): ResourcesV1(True,0,0,0,0)
    def test_float(self):
        with self.assertRaises(ContractError): ResourcesV1(0.0,0,0,0,0)
    def test_overflow(self):
        with self.assertRaises(ContractError): ResourcesV1(MAX+1,0,0,0,0)
    def test_totals(self):
        with self.assertRaisesRegex(ContractError,'BUDGET_TOTAL'): TaskBudgetV1('cog-budget-v1',ResourcesV1(0,0,0,0,0),ResourcesV1(1,0,0,0,0))
    def test_bad_evidence(self):
        with self.assertRaises(ContractError): EvidenceRefV1(ID,'string-is-not-proof',ID,ID)
    def test_schema(self):
        with self.assertRaises(ContractError): replace(initial().task,schema_version='v2')
    def test_mutable_nested(self):
        with self.assertRaises(ContractError): replace(initial().task,steps=[])
    def test_noncanonical(self):
        with self.assertRaisesRegex(ContractError,'NONCANONICAL'): parse_dto(b' '+canonical_bytes(initial()),CognitiveStateV1)
    def test_history_tampering(self):
        s=advance(initial(),'VALIDATE')
        with self.assertRaises(ContractError): replace(s,events=(replace(s.events[0],event_digest='1'*64),))
    def test_bad_identifier(self):
        with self.assertRaises(ContractError): replace(initial().task,task_id='bad')
    def test_bad_timestamp(self):
        with self.assertRaises(ContractError): replace(initial().task,created_at='2026-99-99T00:00:00.000000Z')
    def test_unbounded_text(self):
        with self.assertRaises(ContractError): replace(initial().task,objective='x'*4097)
