import unittest
from dataclasses import replace,FrozenInstanceError
from cognitive_benchmark import *

class Tests(unittest.TestCase):
 def setUp(self):
  self.c=BenchmarkCase('a','EXACT','yes',0,'author','ref');self.s=BenchmarkSuite('suite',(self.c,));self.p=PredictionRecord('a','yes',F(4,5),'ANSWER','candidate','pred');self.o=ObservationRecord('a','yes','observer','obs')
 def runone(self,p=None,**kw):return evaluate(self.s,(self.p if p is None else p,),(self.o,),**kw)
 def bad(self,fn):
  with self.assertRaises((BenchmarkError,TypeError)):fn()
 # Contracts: six
 def test_confidence_boolean(self):self.bad(lambda:replace(self.p,confidence=True))
 def test_confidence_nan(self):self.bad(lambda:replace(self.p,confidence=float('nan')))
 def test_confidence_range(self):self.bad(lambda:replace(self.p,confidence=F(11,10)))
 def test_unknown_field(self):self.bad(lambda:BenchmarkSuite(**dict(asdict_fake=1)))
 def test_version(self):self.bad(lambda:replace(self.s,schema_version='v2'))
 def test_output_validation(self):self.bad(lambda:replace(self.runone(),accuracy=0))
 # Accuracy: six
 def test_correct(self):self.assertEqual(self.runone().accuracy,1)
 def test_incorrect(self):self.assertEqual(self.runone(replace(self.p,answer='no')).accuracy,0)
 def test_numeric_inside(self):
  c=replace(self.c,category='NUMERIC',expected=10,tolerance=2);r=evaluate(replace(self.s,cases=(c,)),(replace(self.p,answer=12),),(replace(self.o,outcome=10),));self.assertEqual(r.accuracy,1)
 def test_numeric_outside(self):
  c=replace(self.c,category='NUMERIC',expected=10,tolerance=2);r=evaluate(replace(self.s,cases=(c,)),(replace(self.p,answer=13),),(replace(self.o,outcome=10),));self.assertEqual(r.accuracy,0)
 def test_aggregate(self):
  r=evaluate(replace(self.s,cases=(self.c,replace(self.c,case_id='b'))),(self.p,),(self.o,replace(self.o,case_id='b')));self.assertEqual(r.accuracy,F(1,2))
 def test_answer_key_mismatch(self):self.bad(lambda:evaluate(self.s,(self.p,),(replace(self.o,outcome='no'),)))
 # Calibration: eight
 def test_brier_known(self):self.assertEqual(self.runone().calibration.brier,F(1,25))
 def test_ece_known(self):self.assertEqual(self.runone().calibration.ece,F(1,5))
 def test_brier_wrong(self):self.assertEqual(self.runone(replace(self.p,answer='no')).calibration.brier,F(16,25))
 def test_bin_boundary(self):self.assertEqual(self.runone().calibration.bins[8],(1,F(4,5),F(1)))
 def test_last_bin(self):self.assertEqual(self.runone(replace(self.p,confidence=1)).calibration.bins[9][0],1)
 def test_overconfidence(self):self.assertEqual(self.runone(replace(self.p,answer='no')).calibration.overconfidence,F(4,5))
 def test_underconfidence(self):self.assertEqual(self.runone().calibration.underconfidence,F(1,5))
 def test_insufficient_samples(self):self.assertFalse(self.runone().calibration.sufficient)
 # Coverage: four
 def test_abstention(self):self.assertEqual(self.runone(replace(self.p,state='ABSTAIN',answer=None,confidence=0)).coverage,0)
 def test_missing(self):self.assertEqual(evaluate(self.s,(),(self.o,)).accuracy,0)
 def test_invalid(self):self.assertEqual(self.runone(replace(self.p,state='INVALID',answer=None,confidence=0)).results[0].state,'INVALID')
 def test_selective(self):self.assertEqual(self.runone().selective_accuracy,1)
 # Regression: six
 def test_accuracy_regression(self):self.assertIn('ACCURACY',compare(self.runone(),self.runone(replace(self.p,answer='no'))).findings)
 def test_calibration_regression(self):self.assertIn('CALIBRATION',compare(self.runone(),self.runone(replace(self.p,confidence=0))).findings)
 def test_abstention_regression(self):self.assertIn('ABSTENTION',compare(self.runone(),self.runone(replace(self.p,state='ABSTAIN',answer=None,confidence=0))).findings)
 def test_invalid_regression(self):self.assertIn('INVALID',compare(self.runone(),self.runone(replace(self.p,state='INVALID',answer=None,confidence=0))).findings)
 def test_missing_regression(self):self.assertIn('MISSING',compare(self.runone(),evaluate(self.s,(),(self.o,))).findings)
 def test_incomparable(self):self.assertEqual(compare(self.runone(),evaluate(replace(self.s,suite_id='other'),(self.p,),(self.o,))).status,'INCOMPARABLE')
 # Determinism: four
 def test_replay(self):self.assertEqual(self.runone(),self.runone())
 def test_commitment(self):self.assertEqual(self.runone().commitment,self.runone().commitment)
 def test_changed_provenance(self):self.assertNotEqual(self.runone().commitment,self.runone(replace(self.p,provenance='new')).commitment)
 def test_immutable(self):
  before=self.p.commitment;self.runone();self.assertEqual(before,self.p.commitment)
  with self.assertRaises(FrozenInstanceError):self.p.answer='no'
 # Safety: six
 def test_stop(self):self.bad(lambda:self.runone(stop=True))
 def test_deadline(self):self.bad(lambda:self.runone(now=1,deadline=1))
 def test_budget(self):self.bad(lambda:self.runone(budget=1))
 def test_case_bound(self):self.bad(lambda:replace(self.s,cases=(self.c,)*1001))
 def test_input_bound(self):self.bad(lambda:replace(self.p,answer='x'*4097))
 def test_independence(self):
  r=self.runone();self.assertEqual(r.independence,'NOT_ESTABLISHED');self.assertFalse(r.production_authorized)
  self.bad(lambda:replace(r,production_authorized=True))

if __name__=='__main__':unittest.main()
