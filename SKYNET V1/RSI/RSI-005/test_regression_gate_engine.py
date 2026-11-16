import unittest
from dataclasses import replace
import test_sandboxed_experimentation as fixture
import regression_gate_engine as engine
from comparative_evaluation_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Tests();self.f.setUp();self.load()
  self.policy=make(EvaluationPolicy,policy_version='v1',permitted_evaluation_types=('DIAGNOSTIC_COMPARISON',),mandatory_gates=GATES,evidence_requirements=('SOURCE_REPLAY','NO_PROVENANCE_UPGRADE'),regression_rules='EXACT_CONSERVATIVE_V1',resource_limits=32,prohibited_operations=e.DENIED,required_authorizations=('NO_ADOPTION_AUTHORITY',))
  self.t=make(RegressionThreshold,metric_id='latency',threshold_type='ABSOLUTE_INTEGER',maximum_allowed_regression=0,minimum_required_improvement=2,threshold_unit='ms',threshold_source='host-policy',qualification_status='HOST_POLICY_DIAGNOSTIC');self.gates=self.build_gates();self.state=engine.initial(self.policy)
 def load(self):
  f=self.f;self.call=(f.spec,f.env,(f.a,f.b),f.call,f.result,f.policy,f.state);self.result=f.go();self.spec=make(EvaluationSpecification,evaluation_id='evaluation',proposal_id='prop-new',experiment_id='exp',baseline_commitment='1'*64,candidate_commitment='2'*64,required_metric_ids=('latency',),required_gate_ids=GATES,evaluation_policy_version='v1',source_commitment=digest(self.result))
 def build_gates(self):return tuple(make(RegressionGate,gate_id=g,gate_type=g,required_metrics=('latency',),threshold_refs=(self.t.commitment,),evidence_requirements=('COMPLETE_SOURCE_REPLAY',),failure_conditions=('ANY_REQUIRED_FAILURE',),inherited_blockers=BLOCKERS) for g in GATES)
 def remake(self,x,**kw):
  v={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};v.update(kw);return make(type(x),**v)
 def go(self,**kw):
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest((self.spec,(self.t,),tuple(sorted(self.gates,key=lambda g:g.gate_id)),self.call,self.result,self.policy)),sequence=self.state.sequence+1);controls.update(kw);return engine.evaluate(self.spec,(self.t,),self.gates,self.call,self.result,self.policy,self.state,**controls)
 def test01_forged(self):
  with self.assertRaises(Exception):replace(self.spec,commitment='0'*64)
 def test02_version(self):
  with self.assertRaises(Exception):self.remake(self.t,schema_version='bad')
 def test03_nan(self):
  with self.assertRaises(Exception):self.remake(self.t,minimum_required_improvement=float('nan'))
 def test04_bool(self):
  with self.assertRaises(Exception):self.remake(self.t,maximum_allowed_regression=True)
 def test05_frozen(self):
  with self.assertRaises(Exception):self.t.minimum_required_improvement=0
 def test06_binding(self):
  self.spec=self.remake(self.spec,proposal_id='wrong')
  with self.assertRaises(Exception):self.go()
 def test07_missing_metric(self):
  self.spec=self.remake(self.spec,required_metric_ids=('other',))
  with self.assertRaises(Exception):self.go()
 def test08_subject(self):
  self.spec=self.remake(self.spec,baseline_commitment='7'*64)
  with self.assertRaises(Exception):self.go()
 def test09_units(self):
  self.t=self.remake(self.t,threshold_unit='seconds');self.gates=self.build_gates()
  with self.assertRaises(Exception):self.go()
 def test10_context(self):
  self.f.b=self.f.remake(self.f.b,measurement_context='other');self.load();self.assertEqual(self.go()[3].decision,'NOT_COMPARABLE')
 def test11_boundary(self):self.assertEqual(dict(self.go()[3].gate_results)['PERFORMANCE_ACCEPTANCE'],'PASS')
 def test12_below_threshold(self):
  self.t=self.remake(self.t,minimum_required_improvement=3);self.gates=self.build_gates();self.assertEqual(dict(self.go()[3].gate_results)['PERFORMANCE_ACCEPTANCE'],'FAIL')
 def test13_regression(self):
  self.f.b=self.f.remake(self.f.b,metric_value=12);self.load();self.assertEqual(self.go()[3].decision,'REGRESSION_DETECTED')
 def test14_no_compatibility_claim(self):self.assertEqual(dict(self.go()[3].gate_results)['INTERFACE_COMPATIBILITY'],'NOT_QUALIFIED')
 def test15_blockers(self):self.assertEqual(dict(self.go()[3].gate_results)['INHERITED_BLOCKERS'],'FAIL')
 def test16_independent(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][0],provenance_class='INDEPENDENTLY_VERIFIED')
 def test17_verified(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][0],verification_status='VERIFIED')
 def test18_contradiction(self):
  self.f.b=self.f.remake(self.f.b,provenance_class='CONTRADICTED');self.load();self.assertEqual(self.go()[3].decision,'EVIDENCE_REQUIRED')
 def test19_suppression(self):
  with self.assertRaises(Exception):self.remake(self.gates[0],inherited_blockers=())
 def test20_relaxation(self):
  with self.assertRaises(Exception):self.remake(self.policy,mandatory_gates=())
 def test21_stop(self):
  with self.assertRaises(Exception):self.go(stop=True)
 def test22_deadline(self):
  with self.assertRaises(Exception):self.go(now=1,deadline=1)
 def test23_stale(self):
  with self.assertRaises(Exception):self.go(expected_state='0'*64)
 def test24_budget(self):
  self.policy=self.remake(self.policy,resource_limits=1);self.state=engine.initial(self.policy)
  with self.assertRaises(Exception):self.go()
 def test25_duplicate(self):
  self.state=self.go()[0]
  with self.assertRaises(Exception):self.go()
 def test26_real_chain(self):self.assertEqual(self.go()[2].source_commitment,digest(self.result))
 def test27_source_forged(self):
  self.spec=self.remake(self.spec,source_commitment='0'*64)
  with self.assertRaises(Exception):self.go()
 def test28_replay(self):self.assertEqual(self.go(),self.go())
 def test29_gate_order(self):
  result=self.go();self.gates=tuple(reversed(self.gates));self.assertEqual(result,self.go())
 def test30_authority(self):
  v=self.go()[3];self.assertTrue(all(x is False for k,x in v.authorization_flags))
  with self.assertRaises(Exception):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
if __name__=='__main__':unittest.main()
