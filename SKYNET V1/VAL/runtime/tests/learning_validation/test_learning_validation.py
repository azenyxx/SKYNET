import unittest,copy
from unittest.mock import patch
from skynet_learning_validation.benchmark import generate,validate
from skynet_learning_validation.adapter import execute,discover
from skynet_learning_validation.validation import run,verify,metrics
from skynet_validation.evidence import Invalid,seal,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.admission=discover();cls.rows,cls.times=run(cls.tasks,cls.admission)
 def kinds(self,*ks):return [e for e in self.rows if e['task']['input']['kind']in ks]
 def good(self,*ks):
  for e in self.kinds(*ks):self.assertEqual(e['status'],'PASS',e)
 def test_grid(self):self.assertEqual(generate(),generate());self.assertEqual(len({t['id'] for t in self.tasks}),48)
 def test_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'LEARN-%03d'%i:8 for i in range(1,7)})
 def test_seeds_and_difficulty(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_experience_recording(self):self.good('record')
 def test_feedback_retention(self):self.good('feedback')
 def test_missing_records(self):self.good('missing')
 def test_invalid_identifiers(self):self.good('invalid_id')
 def test_provenance_rejection(self):self.good('bad_provenance','duplicate_evidence')
 def test_conflicting_feedback(self):self.good('conflicting')
 def test_programmed_retry(self):self.good('retry')
 def test_failed_report_preserved(self):
  for e in self.rows:
   if e['task']['domain']=='LEARN-005':self.assertEqual(e['output']['answer']['retained']['reported_outcome'],'FAILED')
 def test_native_absence_no_execution(self):
  for e in self.rows:
   if e['task']['track']=='native':self.assertEqual(e['status'],'UNAVAILABLE');self.assertIsNone(self.times[e['task']['id']]);self.assertFalse(e['output']['calls'])
 def test_admission_reused(self):
  with patch('skynet_learning_validation.validation.execute',side_effect=AssertionError('NATIVE_EXECUTION')):self.assertEqual(len(run([t for t in self.tasks if t['track']=='native'],self.admission)[0]),32)
 def test_heldout(self):
  for t in self.tasks:self.assertFalse(set(e[0] for e in t['input']['source']['examples'])&set(t['input']['subsequent_input']['values']))
 def test_controls(self):
  for t in self.tasks:self.assertEqual(t['input']['control']['target'],t['input']['subsequent_input']);self.assertIsNone(t['input']['control']['experience'])
 def test_store_control_isolation(self):
  for e in self.rows:
   if e['task']['track']=='infrastructure':d=e['output']['details'];self.assertEqual(d['control_initial_digest'],d['control_final_digest']);self.assertEqual(d['control_result'],'MISSING')
 def test_metrics_not_measured(self):
  m=metrics(self.kinds('improvement','rule','unseen','transfer'),self.admission);self.assertEqual(m['coverage'],0);self.assertIsNone(m['accuracy_executed']);self.assertEqual(m['learning_gain'],'NOT_MEASURED');self.assertEqual(m['generalization_gap'],'NOT_MEASURED')
 def test_track_separation(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows,self.admission)
 def test_evidence_integrity(self):
  for e in self.rows:self.assertTrue(verify(e,self.admission))
 def test_tamper(self):
  e=copy.deepcopy(self.rows[0]);e['expected']=None
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e,self.admission)
 def test_resealed_expected(self):
  e=copy.deepcopy(self.rows[0]);e.pop('evidence_commitment');e['expected']=None
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(seal(e),self.admission)
 def test_storage_and_retry_not_learning(self):
  for original in self.kinds('record','retry'):
   e=copy.deepcopy(original);e.pop('evidence_commitment');e['output']['classification']='LEARNED';e['output_digest']=commitment('val006-output',e['output'])
   with self.assertRaisesRegex(Invalid,'^LEARNING_PROMOTION$'):verify(seal(e),self.admission)
 def test_native_false_pass(self):
  e=copy.deepcopy(self.kinds('rule')[0]);e.pop('evidence_commitment');e['status']='PASS'
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(seal(e),self.admission)
 def test_oracle_isolation(self):
  with patch('skynet_learning_validation.benchmark.reference',side_effect=AssertionError('LEAK')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
 def test_invalid_control_and_duplicates(self):
  t=copy.deepcopy(self.tasks[0]);t['input']['control']['experience']='answer'
  with self.assertRaisesRegex(Invalid,'^CONTROL$'):validate(t)
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([self.tasks[0]]*2,self.admission)
