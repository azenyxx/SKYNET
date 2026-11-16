import unittest,copy
from unittest.mock import patch
from skynet_adaptation_validation.benchmark import generate,validate
from skynet_adaptation_validation.adapter import execute
from skynet_adaptation_validation.validation import run,verify,metrics
from skynet_validation.evidence import Invalid,seal,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.rows,cls.times=run(cls.tasks)
 def kinds(self,*ks):return [e for e in self.rows if e['task']['input']['kind']in ks]
 def good(self,*ks):
  for e in self.kinds(*ks):self.assertEqual(e['status'],'PASS',e)
 def test_generator(self):self.assertEqual(generate(),generate());self.assertEqual(len({t['id'] for t in self.tasks}),48)
 def test_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'ADAPT-%03d'%i:8 for i in range(1,7)})
 def test_variants(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_availability(self):self.good('unavailable','reactivate')
 def test_invalid_state(self):self.good('invalid_status')
 def test_worker_failure(self):self.good('worker_failure')
 def test_requeue(self):self.good('requeue')
 def test_release(self):self.good('release')
 def test_retry_limits(self):self.good('exhausted')
 def test_capacity(self):self.good('capacity')
 def test_priority(self):self.good('priority')
 def test_missing_dependencies(self):self.good('missing','combined_missing')
 def test_cycles(self):self.good('cycle','combined_cycle')
 def test_novel_combinations(self):self.good('combined_priority','combined_dependency');self.assertEqual(sum(t['domain']=='ADAPT-005' for t in self.tasks),8)
 def test_native_absence(self):
  for e in self.kinds('selection','revision'):self.assertEqual(e['status'],'UNAVAILABLE');self.assertFalse(e['output']['calls'])
 def test_track_separation(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows)
 def test_no_native_score(self):
  m=metrics(self.kinds('selection','revision'));self.assertIsNone(m['accuracy_executed']);self.assertEqual(m['autonomous_revision_success'],'NOT_MEASURED');self.assertEqual(m['coverage'],0)
 def test_evidence_integrity(self):
  for e in self.rows:self.assertTrue(verify(e))
 def test_tamper(self):
  e=copy.deepcopy(self.rows[0]);e['status']='PASS' if e['status']!='PASS' else 'FAIL'
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e)
 def test_reference_forgery(self):
  e=copy.deepcopy(self.rows[0]);e.pop('evidence_commitment');e['expected']={'forged':True};e=seal(e)
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(e)
 def test_recovery_not_reasoning(self):
  e=copy.deepcopy(self.kinds('requeue')[0]);e.pop('evidence_commitment');e['output']['level']='AUTONOMOUS';e['output_digest']=commitment('val005-output',e['output']);e=seal(e)
  with self.assertRaisesRegex(Invalid,'^LEVEL_PROMOTION$'):verify(e)
 def test_native_promotion(self):
  e=copy.deepcopy(self.kinds('revision')[0]);e.pop('evidence_commitment');e['status']='PASS';e=seal(e)
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(e)
 def test_oracle_isolation(self):
  with patch('skynet_adaptation_validation.benchmark.reference',side_effect=AssertionError('LEAK')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
 def test_invalid_and_duplicate_inputs(self):
  t=copy.deepcopy(self.tasks[0]);t['input']['priority']=True
  with self.assertRaisesRegex(Invalid,'^NUMBER$'):validate(t)
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([self.tasks[0]]*2)

 def test_deterministic_execution(self):self.assertEqual(run(self.tasks[:1])[0],self.rows[:1])
