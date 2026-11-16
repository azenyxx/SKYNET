import unittest,copy
from unittest.mock import patch
from skynet_metacognition_validation.benchmark import generate,validate
from skynet_metacognition_validation.adapter import execute,discover
from skynet_metacognition_validation.validation import run,verify,metrics
from skynet_validation.evidence import Invalid,seal,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.admission=discover();cls.rows,cls.times=run(cls.tasks,cls.admission)
 def kinds(self,*ks):return [e for e in self.rows if e['task']['input']['kind']in ks]
 def good(self,*ks):
  for e in self.kinds(*ks):self.assertEqual(e['status'],'PASS',e)
 def test_generator(self):self.assertEqual(generate(),generate());self.assertEqual(len({t['id'] for t in self.tasks}),48)
 def test_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'META-%03d'%i:8 for i in range(1,7)})
 def test_seeds_difficulty(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_execution_monitoring(self):self.good('complete','failed','retry')
 def test_heartbeat_monitoring(self):self.good('heartbeat','stale')
 def test_invalid_state(self):self.good('invalid_state')
 def test_missing_evidence(self):self.good('missing_evidence')
 def test_corrupted_evidence(self):self.good('corrupt_evidence')
 def test_failure_categories(self):self.good('WORKER_FAILED','MEMORY_CONFLICT')
 def test_invalid_classifications(self):self.good('invalid_event','invalid_category','unknown_component')
 def test_structural_correction(self):self.good('fixed_binding')
 def test_unsuccessful_correction(self):self.good('bad_again')
 def test_conflict_and_insufficiency(self):self.good('opposite','insufficient')
 def test_terminal_immutability(self):
  for e in self.kinds('fixed_binding','bad_again','opposite','insufficient'):self.assertTrue(e['output']['details']['terminal_unchanged']);self.assertEqual(e['output']['answer']['terminal_rejection'],'TERMINAL')
 def test_rejection_audit(self):
  for e in self.kinds('fixed_binding','bad_again'):self.assertEqual(len(e['output']['details']['rejected_assessments']),e['output']['answer']['rejected']);self.assertIn('EVIDENCE_BINDING',e['output']['details']['rejection_codes'])
 def test_native_absence(self):
  for e in self.kinds('uncertainty','self_correction'):self.assertEqual(e['status'],'UNAVAILABLE');self.assertIsNone(self.times[e['task']['id']]);self.assertFalse(e['output']['calls'])
 def test_absence_not_reexecuted(self):
  with patch('skynet_metacognition_validation.validation.execute',side_effect=AssertionError('FALSE_EXECUTION')):self.assertEqual(len(run([t for t in self.tasks if t['track']=='native'],self.admission)[0]),16)
 def test_track_separation(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows,self.admission)
 def test_native_metrics(self):
  m=metrics(self.kinds('uncertainty','self_correction'),self.admission);self.assertIsNone(m['accuracy_executed']);self.assertEqual(m['autonomous_correction_success'],'NOT_MEASURED');self.assertEqual(m['coverage'],0)
 def test_all_evidence(self):
  for e in self.rows:self.assertTrue(verify(e,self.admission))
 def test_tamper_and_forged_reference(self):
  e=copy.deepcopy(self.rows[0]);e['expected']=None
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e,self.admission)
  e.pop('evidence_commitment')
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(seal(e),self.admission)
 def test_false_native_pass(self):
  e=copy.deepcopy(self.kinds('self_correction')[0]);e.pop('evidence_commitment');e['status']='PASS'
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(seal(e),self.admission)
 def test_programmed_response_not_metacognition(self):
  for row in self.kinds('failed','retry','fixed_binding'):
   e=copy.deepcopy(row);e.pop('evidence_commitment');e['output']['classification']='AUTONOMOUS_CORRECTION';e['output_digest']=commitment('val007-output',e['output'])
   with self.assertRaisesRegex(Invalid,'^METACOGNITION_PROMOTION$'):verify(seal(e),self.admission)
 def test_oracle_isolation(self):
  with patch('skynet_metacognition_validation.benchmark.reference',side_effect=AssertionError('LEAK')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
 def test_invalid_controls_and_duplicates(self):
  t=copy.deepcopy(self.tasks[0]);t['input']['correction_origin']='NATIVE'
  with self.assertRaisesRegex(Invalid,'^CONTROL$'):validate(t)
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([self.tasks[0]]*2,self.admission)
