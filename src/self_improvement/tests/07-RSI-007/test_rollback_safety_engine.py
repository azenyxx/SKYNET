import unittest
from contextlib import contextmanager
from unittest.mock import patch
from agent_contracts import Invalid
from dataclasses import replace
import test_improvement_selection_engine as fixture
import rollback_safety_engine as engine
from versioning_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Tests();self.f.setUp();f=self.f;self.call=(f.entries,f.criteria,f.policy,f.state);self.result=f.go()
  self.source=make(VersionSnapshot,snapshot_id='source',component_id='component',component_version='v1',source_commitment='1'*64,interface_commitments=(),dependency_commitments=(),configuration_commitment='3'*64,provenance_class='REPORTED_ONLY')
  self.target=self.remake(self.source,snapshot_id='target',component_version='candidate-v1',source_commitment='2'*64)
  self.transition=make(VersionTransition,transition_id='transition',proposal_id='prop-new',candidate_id='candidate',source_snapshot_id='source',target_snapshot_id='target',governance_verdict_ref=self.result[3][0].commitment,evaluation_verdict_ref=f.entry[2][3].commitment,compatibility_requirements=('EXACT_DECLARED_INTERFACES','EXACT_DECLARED_DEPENDENCIES'))
  self.dependency=make(VersionDependency,component_id='component',component_version='candidate-v1',required_dependencies=(),interface_constraints=(),compatibility_status='DECLARED_NOT_QUALIFIED',unresolved_dependencies=())
  self.plan=make(RollbackPlan,rollback_id='rollback',transition_id='transition',target_snapshot_id='source',restoration_requirements=('EXACT_SOURCE_SNAPSHOT',),state_compatibility_requirements=('IMMUTABLE_COMMITMENT_EQUALITY_ONLY',),dependency_requirements=(),required_evidence=('HOST_PINNED_RESTORATION_SNAPSHOT',),prohibited_effects=g.q.e.DENIED+('ACTUAL_ROLLBACK',))
  self.policy=make(SafetyValidationPolicy,policy_version='v1',permitted_validation_operations=('SNAPSHOT_COMPARISON','DECLARATIVE_ROLLBACK'),mandatory_safety_gates=GATES,versioning_requirements=('EXACT_SOURCE_BINDING',),rollback_requirements=('NO_ACTUAL_RESTORATION',),evidence_requirements=('ORIGINAL_GOVERNANCE_REPLAY',),inherited_blocker_rules='PRESERVE_ALL',resource_limits=16,prohibited_operations=g.q.e.DENIED+('ACTUAL_ROLLBACK',));self.state=engine.initial(self.policy);self.restoration=(self.source,)
 @contextmanager
 def exact(self,kind,reason):
  state=self.state;pin=state.state_commitment;policy=self.policy;original=self.result
  with self.assertRaisesRegex(kind,reason) as caught:
   yield
  self.assertIs(type(caught.exception),kind)
  self.assertIs(self.state,state);self.assertEqual(self.state.state_commitment,pin)
  self.assertEqual(self.policy,policy);self.assertEqual(self.result,original)
  self.assertTrue(all(value is False for _,value in self.result[3][0].authorization_flags))
 def remake(self,x,**kw):
  values={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};values.update(kw);return make(type(x),**values)
 def go(self,**kw):
  args=(self.source,self.target,self.transition,self.dependency,self.plan,self.restoration,self.call,self.result,self.policy)
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest(args),sequence=self.state.sequence+1);controls.update(kw);return engine.validate(*args,self.state,**controls)
 def test01_source_hash(self):
  with self.exact(ValueError,r'^COMMITMENT$'):replace(self.source,snapshot_commitment='0'*64)
 def test02_target_hash(self):
  with self.exact(ValueError,r'^COMMITMENT$'):replace(self.target,snapshot_commitment='0'*64)
 def test03_schema(self):
  with self.exact(ValueError,r'^VERSION$'):self.remake(self.source,schema_version='bad')
 def test04_depth(self):
  v=()
  for _ in range(34):v=(v,)
  with self.exact(ValueError,r'^R1_SERIALIZATION_DEPTH$'):digest(v)
 def test05_serialization(self):
  check(self.source,VersionSnapshot);self.assertEqual(digest(self.source),digest(self.source));self.assertNotEqual(digest((1,)),digest(('1',)));self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
 def test06_version(self):
  with self.exact(ValueError,r'^INPUT_PIN$'):self.go(approved_input='0'*64)
  self.target=self.remake(self.target,component_version='wrong')
  with self.exact(ValueError,r'^VERSION_MISMATCH$'):self.go()
 def test07_missing_source(self):
  self.source=None
  with self.exact(ValueError,r'^TYPE$'):self.go()
 def test08_proposal(self):
  self.transition=self.remake(self.transition,proposal_id='wrong')
  with self.exact(ValueError,r'^VERDICT_BINDING$'):self.go()
 def test09_governance(self):
  self.transition=self.remake(self.transition,governance_verdict_ref='0'*64)
  with self.exact(ValueError,r'^VERDICT_BINDING$'):self.go()
 def test10_dependency(self):
  self.dependency=self.remake(self.dependency,required_dependencies=('4'*64,));self.assertEqual(self.go()[1].simulation_status,'DEPENDENCY_BLOCKED')
 def test11_simulation(self):self.assertEqual(self.go()[1].simulation_status,'SIMULATION_PASSED')
 def test12_missing_restoration(self):
  self.restoration=();self.assertEqual(self.go()[1].simulation_status,'RESTORATION_EVIDENCE_REQUIRED')
 def test13_state_mismatch(self):
  self.restoration=(self.remake(self.source,configuration_commitment='9'*64),);self.assertEqual(self.go()[1].simulation_status,'SIMULATION_FAILED')
 def test14_forged_success(self):
  sim=self.go()[1]
  with self.exact(ValueError,r'^FALSE_SUCCESS$'):self.remake(sim,observed_simulated_commitment='0'*64)
 def test15_interface(self):
  self.target=self.remake(self.target,interface_commitments=('7'*64,));self.assertEqual(self.go()[1].simulation_status,'STATE_INCOMPATIBLE')
 def test16_no_approval(self):self.assertEqual(self.go()[2].decision,'GOVERNANCE_BLOCKED')
 def test17_gate_failure(self):self.assertEqual(dict(self.go()[2].safety_gate_results)['GOVERNANCE_ELIGIBILITY'],'FAIL')
 def test18_flags(self):
  v=self.go()[2]
  with self.exact(ValueError,r'^AUTHORITY$'):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
 def test19_policy(self):
  with self.exact(ValueError,r'^AUTHORITY$'):self.remake(self.policy,prohibited_operations=())
 def test20_findings(self):
  with self.exact(ValueError,r'^DECISION$'):self.remake(self.go()[2],unresolved_findings=())
 def test21_duplicate(self):
  self.state=self.go()[0]
  with self.exact(ValueError,r'^REPLAY$'):self.go()
 def test22_stale(self):
  with self.exact(ValueError,r'^STATE_PIN$'):self.go(expected_state='0'*64)
 def test23_budget(self):
  self.policy=self.remake(self.policy,resource_limits=1);self.state=engine.initial(self.policy)
  with patch.object(engine.upstream,'select',wraps=engine.upstream.select) as observed:
   with self.exact(Invalid,r'^OPERATION_BUDGET$'):self.go()
   observed.assert_not_called()
 def test24_stop(self):
  with patch.object(engine.upstream,'select',wraps=engine.upstream.select) as observed:
   with self.exact(Invalid,r'^STOPPED$'):self.go(stop=True)
   observed.assert_not_called()
 def test25_deadline(self):
  with patch.object(engine.upstream,'select',wraps=engine.upstream.select) as observed:
   with self.exact(Invalid,r'^DEADLINE$'):self.go(now=1,deadline=1)
   observed.assert_not_called()
 def test26_real_chain(self):self.assertEqual(self.go()[2].governance_status,'NO_ELIGIBLE_CANDIDATE')
 def test27_missing_predecessor(self):
  self.call=()
  with self.exact(ValueError,r'^GOVERNANCE_SOURCE$'):self.go()
 def test28_replay(self):self.assertEqual(self.go(),self.go())
 def test29_measurement_identity(self):
  self.source=self.remake(self.source,source_commitment='8'*64)
  with self.exact(ValueError,r'^MEASURED_SUBJECT_BINDING$'):self.go()
 def test30_forged_nested(self):
  forged=object.__new__(type(self.result[3][0]))
  for f in fields(forged):object.__setattr__(forged,f.name,getattr(self.result[3][0],f.name))
  object.__setattr__(forged,'commitment','0'*64)
  self.result=self.result[:3]+((forged,),)+self.result[4:]
  with self.exact(ValueError,r'^GOVERNANCE_REPLAY$'):self.go()
if __name__=='__main__':unittest.main()
