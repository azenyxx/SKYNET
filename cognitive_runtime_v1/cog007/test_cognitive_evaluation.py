import unittest,json
from pathlib import Path
from dataclasses import replace,asdict
from unittest.mock import patch
from cognitive_contracts import ContractError,canonical_bytes
from cognitive_evaluation_contracts import *
from cognitive_evaluation import *

class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=parse_cases(Path(__file__).with_name('benchmark_cases.json').read_bytes())
        cls.summary=evaluate_suite(cls.cases)
    def test_every_case(self): self.assertEqual((self.summary.total,self.summary.passed,self.summary.failed),(16,16,0))
    def test_positive(self): self.assertEqual(self.summary.positive_success_rate,RateV1(4,4))
    def test_rejections(self): self.assertEqual(self.summary.rejection_detection_rate,RateV1(12,12))
    def test_denominators(self):
        self.assertEqual(self.summary.budget_accuracy,RateV1(16,16))
        self.assertEqual(self.summary.trace_agreement,RateV1(6,6))
        self.assertEqual(self.summary.logical_replay_agreement,RateV1(16,16))
    def test_replay(self):
        self.assertEqual(self.summary.results[0].trace_id,self.summary.results[1].trace_id)
    def test_tamper(self):
        for r in self.summary.results[11:13]: self.assertEqual(r.observed_outcome,'EVIDENCE_REJECTED')
    def test_production(self): self.assertEqual(self.summary.trust_boundary_violations,0)
    def test_trusted(self): self.assertTrue(all(r.positive_semantics for r in self.summary.results))
    def test_no_writes(self):
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError):
            self.assertTrue(evaluate_case(self.cases[14]).passed)
    def test_no_mutation(self): self.assertTrue(all(r.input_unchanged for r in self.summary.results))
    def test_bad_fixture(self):
        with self.assertRaises(ContractError): replace(self.cases[0],fixture_ref='ARBITRARY')
    def test_unknown_scenario(self):
        with self.assertRaises(ContractError): replace(self.cases[0],scenario='RUN_LLM')
    def test_repeat_summary(self): self.assertEqual(self.summary,evaluate_suite(self.cases))
    def test_no_timing_identity(self): self.assertNotIn('runtime',canonical_bytes(self.summary).decode())
    def test_wrong_expectation_fails(self):
        c=replace(self.cases[0],expected_reason='WRONG'); self.assertFalse(evaluate_case(c).passed)
    def test_unknown_fields(self):
        data={'schema_version':'cog-benchmark-cases-v1','cases':[asdict(self.cases[0])|{'unknown':True}]}
        with self.assertRaises(ContractError): parse_cases(json.dumps(data).encode())
    def test_duplicate_case(self):
        with self.assertRaises(ContractError): evaluate_suite((self.cases[0],self.cases[0]))
    def test_duplicate_json(self):
        with self.assertRaises(ContractError): parse_cases(b'{"x":1,"x":2}')
    def test_exceptions(self): self.assertEqual(self.summary.unexpected_exceptions,0)
    def test_empty_denominator(self):
        s=evaluate_suite((self.cases[0],))
        self.assertEqual(s.rejection_detection_rate,RateV1(0,0))
