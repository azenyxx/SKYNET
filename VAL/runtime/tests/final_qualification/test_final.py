import unittest,copy
from pathlib import Path
from skynet_final_qualification.audit import audit
from skynet_final_qualification.qualification import *
from skynet_validation.evidence import Invalid
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.root=Path(__file__).resolve().parents[2];cls.matrix=audit(cls.root);cls.rows=run(cls.matrix)
 def test_stages(self):self.assertEqual(len(self.matrix['stages']),9)
 def test_counts(self):self.assertEqual([s['records'] for s in self.matrix['stages']],[120,144]+[48]*7)
 def test_references(self):
  for x in self.matrix['records']:self.assertTrue((self.root/x['reference'].split('#')[0]).exists());self.assertEqual(len(x['evidence_digest']),64)
 def test_historical(self):self.assertEqual({x['provenance'] for x in self.matrix['records']},{'HISTORICAL_EVIDENCE'})
 def test_matrix_determinism(self):self.assertEqual(self.matrix,audit(self.root))
 def test_grid(self):self.assertEqual(len(cases()),48);self.assertEqual(len({x['id'] for x in cases()}),48)
 def test_domains(self):self.assertEqual([sum(v['case']['domain']=='QUAL-%03d'%i for v in self.rows) for i in range(1,7)],[8]*6)
 def test_fresh(self):self.assertTrue(all(v['result']['status']=='PASS' for v in self.rows[:8]))
 def test_native(self):self.assertTrue(all(v['result']['status']=='UNAVAILABLE' for v in self.rows[-8:]))
 def test_repeat(self):self.assertEqual(self.rows,run(self.matrix))
 def test_q1(self):self.assertEqual(level(self.matrix,self.rows),'Q1')
 def test_failure_q0(self):
  v=copy.deepcopy(self.rows);v[0]['result']['status']='FAIL';self.assertEqual(level(self.matrix,v),'Q0')
 def reject_promotion(self,stage,cap):
  x=next(v for v in self.matrix['records'] if v['stage']==stage and v['capability']==cap)
  with self.assertRaisesRegex(Invalid,'^FALSE_PROMOTION$'):guard(x,'DEMONSTRATED')
 def test_schedule_not_plan(self):self.reject_promotion('VAL-003','PLAN-004')
 def test_retrieval_not_learning(self):self.reject_promotion('VAL-004','MEM-002')
 def test_retry_not_correction(self):self.reject_promotion('VAL-005','ADAPT-002')
 def test_workers_not_autonomy(self):self.reject_promotion('VAL-008','AUTO-002')
 def test_errors_not_reasoning(self):self.reject_promotion('VAL-009','ROBUST-001')
 def test_missing_evidence(self):
  x=dict(self.matrix['records'][0],reference='')
  with self.assertRaisesRegex(Invalid,'^MISSING_EVIDENCE$'):guard(x,x['classification'])
 def test_historical_not_fresh(self):
  x=self.matrix['records'][0]
  with self.assertRaisesRegex(Invalid,'^HISTORICAL_AS_FRESH$'):guard(x,x['classification'],'FRESH_EXECUTION')
 def test_agi_asi(self):
  for q in ('Q2','Q3','Q4'):
   with self.assertRaisesRegex(Invalid,'^UNSUPPORTED_INTELLIGENCE_CLAIM$'):assert_level(q,self.matrix,self.rows)
 def test_unavailable_not_failure(self):self.assertTrue(all(x['classification']=='UNAVAILABLE' for x in self.matrix['records'] if x['claimed_status']=='UNAVAILABLE'))
 def test_native_performance(self):self.assertTrue(all(v['result']['performance']=='NOT_MEASURED' for v in self.rows[-8:]))
 def test_invalid_class(self):
  with self.assertRaisesRegex(Invalid,'^CLASSIFICATION$'):guard(self.matrix['records'][0],'AGI')
 def test_digest_tamper(self):
  from skynet_robustness_validation.validation import verify
  from skynet_final_qualification.audit import read
  d=read(self.root,'VAL-009-EVIDENCE.json');e=copy.deepcopy(d['first'][0]);e['output']['answer']={}
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e,d['admission'])
 def test_no_false_native(self):self.assertFalse(any(v['result']['native_cognition'] for v in self.rows))
