import unittest
from dataclasses import replace
import test_improvement_proposal_engine as fixture
import sandboxed_experimentation as engine
from experiment_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Tests();self.f.setUp();f=self.f;self.call=(f.args,f.result,'hyp-new','prop-new','latency','LOWER','',f.state);self.result=f.go()
  self.policy=make(ExperimentPolicy,policy_version='v1',permitted_experiment_types=TYPES,permitted_measurement_types=('DIAGNOSTIC','REPORTED','UNAVAILABLE'),evidence_requirements=('ORIGINAL_PROPOSAL_REPLAY','NO_AUTHENTICITY_INFERENCE'),comparison_rules='integer-exact-v1',resource_limits=32,prohibited_operations=DENIED,required_authorizations=('NO_ADOPTION_AUTHORITY',))
  self.spec=make(ExperimentSpecification,experiment_id='exp',proposal_id='prop-new',hypothesis_id='hyp-new',target_component='component',target_version='v1',candidate_version='candidate-v1',experiment_type='METRIC_COMPARISON',baseline_ref='1'*64,candidate_ref='2'*64,target_metrics=(('latency','ms','LOWER','fixture'),),success_criteria='IMPROVEMENT_WITHOUT_REGRESSION',falsification_criteria='ANY_REGRESSION_OR_NO_IMPROVEMENT',resource_limits=16,source_commitment=digest(self.result))
  self.env=make(ExperimentEnvironment,environment_id='env',environment_version='v1',runtime_fingerprint='3'*64,dependency_commitments=(),configuration_commitment='4'*64,isolation_class='PURE_DATA_INTERFACE_NO_OS_ISOLATION',permitted_operations=('COMPARE_SUPPLIED_OBSERVATIONS',),prohibited_operations=DENIED)
  self.a=make(ExperimentMeasurement,measurement_id='base',experiment_id='exp',subject_type='BASELINE',subject_commitment='1'*64,component_id='component',component_version='v1',metric_id='latency',metric_value=10,metric_unit='ms',measurement_context='fixture',provenance_class='REPORTED_ONLY',verification_status='DIAGNOSTIC',source_commitment='5'*64)
  self.b=self.remake(self.a,measurement_id='candidate',subject_type='CANDIDATE',subject_commitment='2'*64,component_version='candidate-v1',metric_value=8,source_commitment='6'*64);self.state=engine.initial(self.policy)
 def remake(self,x,**kw):
  v={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};v.update(kw);return make(type(x),**v)
 def go(self,measurements=None,**kw):
  ms=(self.a,self.b) if measurements is None else measurements;ordered=tuple(sorted(ms,key=lambda m:m.measurement_id));controls=dict(expected_state=self.state.state_commitment,approved_input=digest((self.spec,self.env,ordered,self.call,self.result,self.policy)),sequence=self.state.sequence+1);controls.update(kw);return engine.evaluate(self.spec,self.env,ms,self.call,self.result,self.policy,self.state,**controls)
 def test01_forged(self):
  with self.assertRaises(Exception):replace(self.spec,commitment='0'*64)
 def test02_version(self):
  with self.assertRaises(Exception):self.remake(self.spec,schema_version='bad')
 def test03_nan(self):
  with self.assertRaises(Exception):self.remake(self.a,metric_value=float('nan'))
 def test04_bool(self):
  with self.assertRaises(Exception):self.remake(self.a,metric_value=True)
 def test05_frozen(self):
  with self.assertRaises(Exception):self.a.metric_value=0
 def test06_hypothesis(self):
  self.spec=self.remake(self.spec,hypothesis_id='wrong')
  with self.assertRaises(Exception):self.go()
 def test07_proposal(self):
  self.spec=self.remake(self.spec,source_commitment='0'*64)
  with self.assertRaises(Exception):self.go()
 def test08_subject(self):
  self.b=self.remake(self.b,subject_commitment='7'*64)
  with self.assertRaises(Exception):self.go()
 def test09_units(self):
  self.b=self.remake(self.b,metric_unit='seconds');self.assertEqual(self.go()[3].observed_outcome,'NOT_COMPARABLE')
 def test10_context(self):
  self.b=self.remake(self.b,measurement_context='other');self.assertEqual(self.go()[3].observed_outcome,'NOT_COMPARABLE')
 def test11_improve(self):self.assertEqual(self.go()[3].observed_outcome,'IMPROVEMENT_OBSERVED')
 def test12_regress(self):
  self.b=self.remake(self.b,metric_value=12);self.assertEqual(self.go()[3].observed_outcome,'REGRESSION_OBSERVED')
 def test13_equal(self):
  self.b=self.remake(self.b,metric_value=10);self.assertEqual(self.go()[3].observed_outcome,'NO_MEASURABLE_CHANGE')
 def test14_missing(self):self.assertEqual(self.go(measurements=(self.b,))[3].observed_outcome,'EVIDENCE_REQUIRED')
 def test15_hidden_regression(self):
  self.spec=self.remake(self.spec,target_metrics=self.spec.target_metrics+(('memory','bytes','LOWER','fixture'),));a=self.remake(self.a,measurement_id='mem-base',metric_id='memory',metric_unit='bytes',source_commitment='8'*64);b=self.remake(self.b,measurement_id='mem-candidate',metric_id='memory',metric_unit='bytes',metric_value=20,source_commitment='9'*64);self.assertEqual(self.go(measurements=(self.a,self.b,a,b))[3].observed_outcome,'REGRESSION_OBSERVED')
 def test16_independent(self):
  with self.assertRaises(Exception):self.remake(self.a,provenance_class='INDEPENDENTLY_VERIFIED')
 def test17_verified(self):
  with self.assertRaises(Exception):self.remake(self.a,verification_status='VERIFIED')
 def test18_duplicates(self):
  with self.assertRaises(Exception):self.go(measurements=(self.a,self.a,self.b))
 def test19_contradictory(self):
  self.b=self.remake(self.b,provenance_class='CONTRADICTED');self.assertEqual(self.go()[3].observed_outcome,'INCONCLUSIVE')
 def test20_policy(self):
  with self.assertRaises(Exception):self.remake(self.env,permitted_operations=('SHELL',))
 def test21_stop(self):
  with self.assertRaises(Exception):self.go(stop=True)
 def test22_deadline(self):
  with self.assertRaises(Exception):self.go(now=1,deadline=1)
 def test23_stale(self):
  with self.assertRaises(Exception):self.go(expected_state='0'*64)
 def test24_budget(self):
  self.spec=self.remake(self.spec,resource_limits=1)
  with self.assertRaises(Exception):self.go()
 def test25_duplicate_experiment(self):
  self.state=self.go()[0]
  with self.assertRaises(Exception):self.go()
 def test26_real_chain(self):self.assertEqual(self.go()[3].evidence_qualification,'NOT_INDEPENDENTLY_QUALIFIED')
 def test27_tampered_result(self):
  self.result=(self.result[0],self.result[1][:-1])
  with self.assertRaises(Exception):self.go()
 def test28_all_flags(self):self.assertTrue(all(v is False for k,v in self.go()[3].authorization_flags))
 def test29_findings(self):
  self.assertEqual(self.go()[3].unresolved_findings,BLOCKERS)
  with self.assertRaises(Exception):self.remake(self.go()[2],unresolved_blockers=())
 def test30_reorder(self):self.assertEqual(self.go(),self.go(measurements=(self.b,self.a)))
if __name__=='__main__':unittest.main()
