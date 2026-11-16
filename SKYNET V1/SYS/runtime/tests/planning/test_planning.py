import copy,unittest
from unittest.mock import patch
from skynet_planning_validation.benchmark import generate,graph_reference
from skynet_planning_validation.contracts import validate
from skynet_planning_validation.adapter import execute
from skynet_planning_validation.runner import run,verify,metrics
from skynet_validation.evidence import Invalid,commitment
class PlanningTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.tasks=generate();cls.results,cls.times=run(cls.tasks)
 def rows(self,d,kind=None):return [e for e in self.results if e['task']['domain']==d and (kind is None or e['task']['input']['kind']==kind)]
 def test_generator_determinism(self):self.assertEqual(generate(),generate())
 def test_unique_cases(self):self.assertEqual(len({t['id'] for t in self.tasks}),48)
 def test_minimum_domains(self):self.assertEqual({d:sum(t['domain']==d for t in self.tasks) for d in {t['domain'] for t in self.tasks}},{'PLAN-%03d'%d:8 for d in range(1,7)})
 def test_goal_representation(self):
  for e in self.rows('PLAN-001'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['required_outcome'],e['task']['input']['value'])
 def test_autonomous_absence(self):self.assertEqual({e['status'] for e in self.rows('PLAN-002')},{'UNAVAILABLE'})
 def test_absence_not_reexecuted(self):self.assertEqual(sum(self.times[e['task']['id']] is not None for e in self.rows('PLAN-002')),1)
 def test_cycles(self):
  for e in self.rows('PLAN-003','cycle'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['code'],'CYCLE');self.assertTrue(e['output']['answer']['unchanged_on_rejection'])
 def test_missing_dependencies(self):
  for e in self.rows('PLAN-003','missing'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['code'],'UNKNOWN_DEPENDENCY')
 def test_valid_graphs(self):
  for e in self.rows('PLAN-003','valid'):self.assertEqual(e['status'],'PASS');self.assertTrue(e['output']['answer']['accepted'])
 def test_capacity(self):
  for e in self.rows('PLAN-004','capacity'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['running'],1)
 def test_unavailable_worker(self):
  for e in self.rows('PLAN-004','unavailable'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['running'],0)
 def test_priority(self):
  for e in self.rows('PLAN-004','capacity'):
   x=e['task']['input'];winner=max(range(x['count']),key=lambda i:(x['priorities'][i],-i));self.assertEqual(e['output']['answer']['states'][winner],'RUNNING')
 def test_real_dependent_execution(self):
  for e in self.rows('PLAN-005','success'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['completed'],e['task']['input']['count']);self.assertIn('skynet_sys_workers.Orchestrator.complete',e['output']['calls'])
 def test_failure_propagation(self):
  for e in self.rows('PLAN-005','failure'):self.assertEqual(e['status'],'PASS');self.assertTrue(e['output']['answer']['failure_propagated'])
 def test_worker_failure_recovery(self):
  for e in self.rows('PLAN-006','worker_failure'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['attempt'],2)
 def test_requeue_retry(self):
  for e in self.rows('PLAN-006','requeue'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['scheduler'],'SUCCEEDED')
 def test_release_lease(self):
  for e in self.rows('PLAN-006','release'):self.assertEqual(e['status'],'PASS');self.assertEqual(e['output']['answer']['stale_code'],'LEASE_STATE')
 def test_reference_cycles(self):self.assertEqual(graph_reference({'a':['b'],'b':['a']}),'CYCLE');self.assertEqual(graph_reference({'a':[],'b':['a']}),'OK')
 def test_reference_missing(self):self.assertEqual(graph_reference({'a':['b']}),'UNKNOWN_DEPENDENCY')
 def test_oracle_not_adapter(self):
  with patch('skynet_planning_validation.benchmark.reference',side_effect=AssertionError('LEAK')):self.assertEqual(execute(self.tasks[0])['status'],'EXECUTED')
 def test_cross_track_scores(self):
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(self.results)
 def test_unavailable_denominators(self):
  m=metrics(self.rows('PLAN-002'));self.assertEqual(m['coverage']['value'],0);self.assertIsNone(m['accuracy_executed']['value'])
 def test_evidence_tamper(self):
  e=copy.deepcopy(self.results[0]);e['output']['answer']['required_outcome']=0
  with self.assertRaisesRegex(Invalid,'^EVIDENCE$'):verify(e)
 def test_native_promotion(self):
  e=copy.deepcopy(self.rows('PLAN-002')[0]);e.pop('digest');e['output']={'status':'EXECUTED','answer':None,'calls':['fake'],'details':{}};e['output']['provenance']=commitment('val003-observed',{'calls':['fake'],'details':{}});e['output_digest']=commitment('val003-output',e['output']);e['status']='PASS';e['digest']=commitment('val003-evidence',e)
  with self.assertRaisesRegex(Invalid,'^TRACK_PROMOTION$'):verify(e)
 def test_invalid_task(self):
  t=copy.deepcopy(self.tasks[0]);t['input']['count']=True
  with self.assertRaisesRegex(Invalid,'^COUNT$'):execute(t)
 def test_duplicate_cases(self):
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([self.tasks[0]]*2)
 def test_all_evidence(self):
  for e in self.results:self.assertTrue(verify(e))
 def test_no_planner_claim(self):self.assertIsNone(metrics(self.rows('PLAN-006'))['autonomous_plan_revision_success'])
 def test_forged_expected_acceptance(self):
  e=copy.deepcopy(self.rows('PLAN-003','cycle')[0]);e.pop('digest');e['expected']={'code':'OK','accepted':True,'unchanged_on_rejection':None};e['output']['answer']=e['expected'];e['output_digest']=commitment('val003-output',e['output']);e['digest']=commitment('val003-evidence',e)
  with self.assertRaisesRegex(Invalid,'^REFERENCE_BINDING$'):verify(e)
 def test_completion_metric(self):
  rows=self.rows('PLAN-005');m=metrics(rows);self.assertEqual(m['execution_completion_rate']['numerator'],sum(e['task']['input']['count'] for e in rows if e['task']['input']['kind']=='success'));self.assertLess(m['execution_completion_rate']['value'],1)
if __name__=='__main__':unittest.main()
