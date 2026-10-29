import unittest
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
 def remake(self,x,**kw):
  values={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};values.update(kw);return make(type(x),**values)
 def go(self,**kw):
  args=(self.source,self.target,self.transition,self.dependency,self.plan,self.restoration,self.call,self.result,self.policy)
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest(args),sequence=self.state.sequence+1);controls.update(kw);return engine.validate(*args,self.state,**controls)
 def test01_source_hash(self):
  with self.assertRaises(Exception):replace(self.source,snapshot_commitment='0'*64)
 def test02_target_hash(self):
  with self.assertRaises(Exception):replace(self.target,snapshot_commitment='0'*64)
 def test03_schema(self):
  with self.assertRaises(Exception):self.remake(self.source,schema_version='bad')
 def test04_frozen(self):
  with self.assertRaises(Exception):self.source.component_version='new'
 def test05_false_provenance(self):
  with self.assertRaises(Exception):self.remake(self.source,provenance_class='INDEPENDENTLY_VERIFIED')
 def test06_version(self):
  self.target=self.remake(self.target,component_version='wrong')
  with self.assertRaises(Exception):self.go()
 def test07_missing_source(self):
  self.source=None
  with self.assertRaises(Exception):self.go()
 def test08_proposal(self):
  self.transition=self.remake(self.transition,proposal_id='wrong')
  with self.assertRaises(Exception):self.go()
 def test09_governance(self):
  self.transition=self.remake(self.transition,governance_verdict_ref='0'*64)
  with self.assertRaises(Exception):self.go()
 def test10_dependency(self):
  self.dependency=self.remake(self.dependency,required_dependencies=('4'*64,));self.assertEqual(self.go()[1].simulation_status,'DEPENDENCY_BLOCKED')
 def test11_simulation(self):self.assertEqual(self.go()[1].simulation_status,'SIMULATION_PASSED')
 def test12_missing_restoration(self):
  self.restoration=();self.assertEqual(self.go()[1].simulation_status,'RESTORATION_EVIDENCE_REQUIRED')
 def test13_state_mismatch(self):
  self.restoration=(self.remake(self.source,configuration_commitment='9'*64),);self.assertEqual(self.go()[1].simulation_status,'SIMULATION_FAILED')
 def test14_forged_success(self):
  sim=self.go()[1]
  with self.assertRaises(Exception):self.remake(sim,observed_simulated_commitment='0'*64)
 def test15_interface(self):
  self.target=self.remake(self.target,interface_commitments=('7'*64,));self.assertEqual(self.go()[1].simulation_status,'STATE_INCOMPATIBLE')
 def test16_no_approval(self):self.assertEqual(self.go()[2].decision,'GOVERNANCE_BLOCKED')
 def test17_gate_failure(self):self.assertEqual(dict(self.go()[2].safety_gate_results)['GOVERNANCE_ELIGIBILITY'],'FAIL')
 def test18_flags(self):
  v=self.go()[2]
  with self.assertRaises(Exception):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
 def test19_policy(self):
  with self.assertRaises(Exception):self.remake(self.policy,prohibited_operations=())
 def test20_findings(self):
  with self.assertRaises(Exception):self.remake(self.go()[2],unresolved_findings=())
 def test21_duplicate(self):
  self.state=self.go()[0]
  with self.assertRaises(Exception):self.go()
 def test22_stale(self):
  with self.assertRaises(Exception):self.go(expected_state='0'*64)
 def test23_budget(self):
  self.policy=self.remake(self.policy,resource_limits=1);self.state=engine.initial(self.policy)
  with self.assertRaises(Exception):self.go()
 def test24_stop(self):
  with self.assertRaises(Exception):self.go(stop=True)
 def test25_deadline(self):
  with self.assertRaises(Exception):self.go(now=1,deadline=1)
 def test26_real_chain(self):self.assertEqual(self.go()[2].governance_status,'NO_ELIGIBLE_CANDIDATE')
 def test27_missing_predecessor(self):
  self.call=()
  with self.assertRaises(Exception):self.go()
 def test28_replay(self):self.assertEqual(self.go(),self.go())
 def test29_measurement_identity(self):
  self.source=self.remake(self.source,source_commitment='8'*64)
  with self.assertRaises(Exception):self.go()
 def test30_forged_result(self):
  self.result=self.result[:-1]+('APPROVED',)
  with self.assertRaises(Exception):self.go()
if __name__=='__main__':unittest.main()
