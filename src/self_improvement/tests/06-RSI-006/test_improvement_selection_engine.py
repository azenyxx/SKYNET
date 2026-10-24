import unittest
from dataclasses import replace
import test_regression_gate_engine as fixture
import improvement_selection_engine as engine
from governance_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Tests();self.f.setUp();self.entry=self.load(self.f,'candidate');self.entries=(self.entry,)
  self.policy=make(GovernancePolicy,policy_version='v1',permitted_selection_operations=('ADVISORY_REVIEW',),mandatory_gate_requirements=q.GATES,minimum_evidence_requirements=('ORIGINAL_SOURCE_REPLAY','NO_AUTHENTICITY_UPGRADE'),inherited_blocker_rules='PRESERVE_ALL_BLOCKING',prohibited_operations=q.e.DENIED,resource_limits=32,required_approval_classes=('EXTERNAL_APPROVAL_NOT_IMPLEMENTED',))
  self.criteria=tuple(make(SelectionCriterion,criterion_id=k,criterion_type=k,comparison_direction='CONSERVATIVE_ORDINAL',evidence_requirements=('ORIGINAL_GATE_REPLAY',),qualification_status='DIAGNOSTIC_ONLY',policy_source='v1') for k in CRITERIA);self.state=engine.initial(self.policy)
 def load(self,f,name):
  call=(f.spec,(f.t,),f.gates,f.call,f.result,f.policy,f.state);result=f.go();proposal=f.call[4][1][3]
  candidate=make(SelectionCandidate,candidate_id=name,proposal_id=proposal.proposal_id,proposal_commitment=proposal.commitment,evaluation_id=f.spec.evaluation_id,evaluation_commitment=digest(result),target_component=proposal.target_component,target_version=proposal.target_version,evidence_refs=(result[2].evidence_id,),inherited_findings=BLOCKERS)
  return candidate,call,result,()
 def remake(self,x,**kw):
  values={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};values.update(kw);return make(type(x),**values)
 def change(self,**kw):self.entries=( (self.remake(self.entry[0],**kw),)+self.entry[1:], )
 def go(self,**kw):
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest((tuple(sorted(self.entries,key=lambda x:x[0].candidate_id)),tuple(sorted(self.criteria,key=lambda c:c.criterion_id)),self.policy)),sequence=self.state.sequence+1);controls.update(kw);return engine.select(self.entries,self.criteria,self.policy,self.state,**controls)
 def auth(self,**kw):
  values=dict(authorization_id='approval',candidate_id='candidate',authorization_class='DESCRIPTIVE_EXTERNAL_CLAIM',issuer_reference='human-claim',authorization_scope=('ADVISORY_REVIEW_ONLY',),authorization_status='NOT_QUALIFIED',provenance_class='REPORTED_ONLY',source_commitment='1'*64);values.update(kw);return make(AuthorizationRecord,**values)
 def test01_forged(self):
  with self.assertRaises(Exception):replace(self.entry[0],commitment='0'*64)
 def test02_version(self):
  with self.assertRaises(Exception):self.remake(self.policy,schema_version='bad')
 def test03_bool(self):
  with self.assertRaises(Exception):self.remake(self.policy,resource_limits=True)
 def test04_frozen(self):
  with self.assertRaises(Exception):self.entry[0].candidate_id='x'
 def test05_invalid_id(self):
  with self.assertRaises(Exception):self.change(candidate_id='')
 def test06_no_eligible(self):self.assertEqual(self.go()[-1],'NO_ELIGIBLE_CANDIDATE')
 def test07_failed_gate(self):self.assertEqual(self.go()[1][0].mandatory_gate_status,'FAIL')
 def test08_preserve_restriction(self):self.assertEqual(self.go()[3][0].decision,'INTEGRATION_NOT_QUALIFIED')
 def test09_regression(self):
  self.f.f.b=self.f.f.remake(self.f.f.b,metric_value=12);self.f.load();self.entries=(self.load(self.f,'candidate'),);self.assertEqual(self.go()[3][0].decision,'RISK_BLOCKED')
 def test10_missing_gate(self):
  with self.assertRaises(Exception):self.remake(self.policy,mandatory_gate_requirements=q.GATES[:-1])
 def test11_ranking(self):self.assertEqual(self.go()[2][0].eligibility_class,'INELIGIBLE')
 def test12_missing_cost(self):self.assertEqual(dict(self.go()[2][0].criterion_results)['RESOURCE_COST'],'MISSING')
 def test13_criteria_order(self):
  expected=self.go();self.criteria=tuple(reversed(self.criteria));self.assertEqual(expected,self.go())
 def test14_duplicate_evidence(self):
  with self.assertRaises(Exception):self.change(evidence_refs=('evaluation','evaluation'))
 def test15_replay_stable(self):self.assertEqual(self.go(),self.go())
 def test16_self_auth(self):
  with self.assertRaises(Exception):self.auth(issuer_reference='candidate')
 def test17_forged_approval(self):
  with self.assertRaises(Exception):self.auth(authorization_status='APPROVED')
 def test18_approval_no_power(self):
  self.entries=(self.entry[:3]+((self.auth(),),),);self.assertEqual(self.go()[-1],'NO_ELIGIBLE_CANDIDATE')
 def test19_flags(self):
  v=self.go()[3][0]
  with self.assertRaises(Exception):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
 def test20_suppression(self):
  with self.assertRaises(Exception):self.change(inherited_findings=())
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
 def test26_real_chain(self):self.assertEqual(self.go()[1][0].evidence_status,'NOT_INDEPENDENTLY_QUALIFIED')
 def test27_proposal(self):
  self.change(proposal_commitment='0'*64)
  with self.assertRaises(Exception):self.go()
 def test28_evaluation(self):
  self.change(evaluation_commitment='0'*64)
  with self.assertRaises(Exception):self.go()
 def test29_identity(self):
  self.change(evaluation_id='wrong')
  with self.assertRaises(Exception):self.go()
 def test30_missing_source(self):
  self.entries=((self.entry[0],(),self.entry[2],()),)
  with self.assertRaises(Exception):self.go()
if __name__=='__main__':unittest.main()
