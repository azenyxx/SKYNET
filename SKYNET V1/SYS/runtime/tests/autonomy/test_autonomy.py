import unittest,copy
from unittest.mock import patch
from skynet_autonomy_validation.cases import generate,validate
from skynet_autonomy_validation.adapter import execute,discover
from skynet_autonomy_validation.validation import run,verify,metrics
from skynet_validation.evidence import Invalid,seal,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.admission=discover();cls.rows,cls.times=run(cls.tasks,cls.admission)
 def kinds(self,*ks):return [e for e in self.rows if e['task']['input']['kind']in ks]
 def good(self,*ks):
  for e in self.kinds(*ks):self.assertEqual(e['status'],'PASS',e)
 def test_generator(self):self.assertEqual(generate(),generate());self.assertEqual(len({t['id'] for t in self.tasks}),48)
 def test_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'AUTO-%03d'%i:8 for i in range(1,7)})
 def test_seeds_difficulty(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_admission(self):self.good('valid')
 def test_authorization(self):self.good('unauthorized')
 def test_duplicate_and_malformed(self):self.good('duplicate','invalid_id')
 def test_dependencies(self):self.good('missing')
 def test_completion(self):self.good('complete')
 def test_no_hidden_progress(self):self.good('pending')
 def test_stale_attempt(self):self.good('stale_attempt')
 def test_unavailable_worker(self):self.good('unavailable')
 def test_workflow_success(self):self.good('success')
 def test_workflow_failure(self):self.good('failure')
 def test_operational_selection(self):self.good('priority','capacity','combined_dependency')
 def test_recovery(self):self.good('worker_failure','requeue','release','exhausted')
 def test_expiration_and_invalid_recovery(self):self.good('lease_expired','invalid_retry')
 def test_native_absence(self):
  for e in self.kinds('goal'):self.assertEqual(e['status'],'UNAVAILABLE');self.assertIsNone(self.times[e['task']['id']]);self.assertFalse(e['output']['calls'])
 def test_absence_not_executed(self):
  with patch('skynet_autonomy_validation.validation.execute',side_effect=AssertionError('FALSE_EXECUTION')):self.assertEqual(len(run([t for t in self.tasks if t['track']=='native'],self.admission)[0]),8)
 def test_track_separation(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows,self.admission)
 def test_native_metrics(self):
  m=metrics(self.kinds('goal'),self.admission);self.assertEqual(m['coverage'],0);self.assertIsNone(m['accuracy_executed']);self.assertEqual(m['native_goal_completion'],'NOT_MEASURED')
 def test_all_evidence(self):
  for e in self.rows:self.assertTrue(verify(e,self.admission))
 def test_tamper_reference(self):
  e=copy.deepcopy(self.rows[0]);e['expected']=None
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e,self.admission)
  e.pop('evidence_commitment')
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(seal(e),self.admission)
 def test_host_plan_not_native(self):
  for row in self.kinds('success','requeue'):
   e=copy.deepcopy(row);e.pop('evidence_commitment');e['output']['classification']='NATIVE_AUTONOMY';e['output_digest']=commitment('val008-output',e['output'])
   with self.assertRaisesRegex(Invalid,'^AUTONOMY_PROMOTION$'):verify(seal(e),self.admission)
 def test_native_false_pass(self):
  e=copy.deepcopy(self.kinds('goal')[0]);e.pop('evidence_commitment');e['status']='PASS'
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(seal(e),self.admission)
 def test_oracle_and_controls(self):
  with patch('skynet_autonomy_validation.reference.expected',side_effect=AssertionError('LEAK')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
  t=copy.deepcopy(self.tasks[0]);t['input']['plan_origin']='NATIVE'
  with self.assertRaisesRegex(Invalid,'^CONTROL$'):validate(t)
