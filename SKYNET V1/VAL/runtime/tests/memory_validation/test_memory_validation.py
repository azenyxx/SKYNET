import unittest,copy
from unittest.mock import patch
from skynet_memory_validation.benchmark import generate,validate,reference
from skynet_memory_validation.adapter import execute
from skynet_memory_validation.runner import run,verify,metrics
from skynet_validation.evidence import Invalid,commitment
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.rows,cls.times=run(cls.tasks)
 def kind(self,k):return [e for e in self.rows if e['task']['input']['kind']==k]
 def good(self,k):
  for e in self.kind(k):self.assertEqual(e['status'],'PASS',e)
 def test_generation(self):self.assertEqual(generate(),generate());self.assertEqual(len(self.tasks),48)
 def test_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'MEM-%03d'%d:8 for d in range(1,7)})
 def test_seeds_difficulty(self):self.assertEqual({t['seed'] for t in self.tasks},{1001,2003});self.assertEqual(len({t['difficulty'] for t in self.tasks}),3)
 def test_create(self):self.good('create')
 def test_duplicate_idempotency(self):self.good('duplicate')
 def test_invalid_id(self):self.good('invalid_id')
 def test_conflicting_duplicate(self):self.good('conflicting_duplicate')
 def test_retrieval(self):self.good('lookup');self.good('many')
 def test_missing(self):self.good('missing')
 def test_invalid_lookup(self):self.good('invalid_lookup')
 def test_updates(self):self.good('update')
 def test_cas_conflicts(self):self.good('cas');self.good('stale')
 def test_restore(self):self.good('restore')
 def test_snapshot_integrity(self):self.good('snapshot');self.good('tamper')
 def test_provenance(self):self.good('bad_provenance');self.good('duplicate_evidence')
 def test_unverified_not_promoted(self):
  self.good('unverified')
  for e in self.kind('unverified'):self.assertEqual(e['output']['answer']['evidence_status'],'UNVERIFIED')
 def test_native_absence(self):
  for k in ('context','transfer'):
   for e in self.kind(k):self.assertEqual(e['status'],'UNAVAILABLE');self.assertFalse(e['output']['calls']);self.assertFalse(e['output']['details']['conditions_executed'])
 def test_transfer_controls(self):
  for t in self.tasks:
   if t['track']=='native':self.assertNotEqual(t['input']['source']['task'],t['input']['target']['task']);self.assertFalse(t['input']['control']['prior_information']);self.assertEqual(t['input']['control']['target'],'identical');self.assertEqual(t['input']['isolation'],'fresh-condition-instances')
 def test_oracle_separation(self):
  with patch('skynet_memory_validation.benchmark.reference',side_effect=AssertionError('ORACLE')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
 def test_tracks(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.rows)
 def test_scoring(self):
  m=metrics([e for e in self.rows if e['track']=='native']);self.assertEqual(m['coverage'],0);self.assertIsNone(m['accuracy_executed']);self.assertEqual(m['transfer_gain'],'NOT_MEASURED');self.assertFalse(m['learning_demonstrated'])
 def test_evidence(self):
  for e in self.rows:self.assertTrue(verify(e))
 def test_corrupted_evidence(self):
  e=copy.deepcopy(self.rows[0]);e['output']['answer']['value']=-1
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e)
 def test_forged_expected(self):
  e=copy.deepcopy(self.rows[0]);e.pop('digest');e['expected']={'value':-1};e['digest']=commitment('val004-evidence',e)
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(e)
 def test_invalid_input(self):
  t=copy.deepcopy(self.tasks[0]);t['input']['value']=True
  with self.assertRaisesRegex(Invalid,'^VALUE$'):validate(t)
 def test_duplicate_cases(self):
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([self.tasks[0]]*2)
 def test_determinism(self):self.assertEqual(run(self.tasks[:2])[0],self.rows[:2])
 def test_native_promotion(self):
  e=copy.deepcopy(self.kind('transfer')[0]);e.pop('digest');e['status']='PASS';e['digest']=commitment('val004-evidence',e)
  with self.assertRaisesRegex(Invalid,'^NATIVE_PROMOTION$'):verify(e)

 def test_malformed_control(self):
  t=copy.deepcopy(next(t for t in self.tasks if t['track']=='native'));t['input']['control']['prior_information']=True
  with self.assertRaisesRegex(Invalid,'^CONTROL$'):validate(t)
 def test_false_infrastructure_absence(self):
  e=copy.deepcopy(self.rows[0]);e.pop('digest');e['status']='UNAVAILABLE';e['digest']=commitment('val004-evidence',e)
  with self.assertRaisesRegex(Invalid,'^INFRASTRUCTURE_ABSENCE$'):verify(e)
