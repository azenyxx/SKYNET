import unittest,copy
from unittest.mock import patch
from skynet_robustness_validation.cases import generate,validate
from skynet_robustness_validation.adapter import execute,discover
from skynet_robustness_validation.validation import run,verify,metrics
from skynet_validation.evidence import Invalid,seal,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.admission=discover();cls.rows,cls.times=run(cls.tasks,cls.admission)
 def kinds(self,*ks):return [e for e in self.rows if e['task']['input']['kind']in ks]
 def good(self,*ks):
  for e in self.kinds(*ks):self.assertEqual(e['status'],'PASS',e)

 def test_generator(self):self.assertEqual(generate(),generate());self.assertEqual(len(self.tasks),48)
 def test_domains(self):self.assertEqual([sum(t['domain']==d for t in self.tasks) for d in sorted({t['domain'] for t in self.tasks})],[8]*6)
 def test_seeds(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_schema(self):self.good(*('schema',))
 def test_missing_field(self):self.good(*('missing_field',))
 def test_type(self):self.good(*('wrong_type',))
 def test_identifier(self):self.good(*('invalid_id',))
 def test_authorization(self):self.good(*('unauthorized',))
 def test_operation(self):self.good(*('unsupported', 'arity'))
 def test_dependencies(self):self.good(*('missing', 'cycle'))
 def test_incomplete(self):self.good(*('pending', 'insufficient', 'opposite'))
 def test_failures(self):self.good(*('worker_failure', 'failure'))
 def test_recovery(self):self.good(*('requeue', 'release', 'exhausted', 'invalid_retry'))
 def test_expiry(self):self.good(*('lease_expired',))
 def test_corruption(self):self.good(*('tamper', 'bad_provenance', 'corrupt_evidence'))
 def test_duplicate(self):self.good(*('duplicate', 'duplicate_evidence', 'conflicting_duplicate'))
 def test_stale(self):self.good(*('stale', 'invalid_state', 'bad_again'))
 def test_resources(self):self.good(*('capacity', 'priority', 'unavailable', 'concurrency', 'queue'))
 def test_native(self):
  for e in self.kinds('uncertainty'):self.assertEqual(e['status'],'UNAVAILABLE');self.assertFalse(e['output']['calls'])
 def test_isolation(self):
  with patch('skynet_robustness_validation.validation.execute',side_effect=AssertionError('LEAK')):self.assertEqual(len(run([t for t in self.tasks if t['track']=='native'],self.admission)[0]),8)
 def test_tracks(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows,self.admission)
 def test_scores(self):
  m=metrics(self.kinds('uncertainty'),self.admission);self.assertEqual(m['coverage'],0);self.assertEqual(m['native_uncertainty_performance'],'NOT_MEASURED')
 def test_evidence(self):
  for e in self.rows:self.assertTrue(verify(e,self.admission))
 def test_tamper(self):
  e=copy.deepcopy(self.rows[0]);e['expected']=None
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e,self.admission)
  e.pop('evidence_commitment')
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(seal(e),self.admission)
 def test_false_native(self):
  e=copy.deepcopy(self.kinds('uncertainty')[0]);e.pop('evidence_commitment');e['status']='PASS'
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(seal(e),self.admission)
