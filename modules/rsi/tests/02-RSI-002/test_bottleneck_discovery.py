import unittest
from dataclasses import replace
import bottleneck_discovery as b
from self_assessment_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.e=r.make(r.ImprovementEvidence,evidence_id='e',source_stage='LRN-008',source_artifact='diagnostic',evidence_type='LOCAL_DIAGNOSTIC',provenance_class='REPORTED_ONLY',source_commitment='1'*64,verification_status='NOT_QUALIFIED',limitations=('INDEPENDENT_PROVENANCE_UNAVAILABLE',))
  self.o=r.make(r.ImprovementObservation,observation_id='obs',component_id='component',component_version='v1',observation_type='DEFICIENCY',evidence_refs=('e',),observed_metrics=(),confidence=(1,2),provenance_class='REPORTED_ONLY',source_commitment=r.digest((self.e,)))
  self.h=r.make(r.ImprovementHypothesis,hypothesis_id='hyp',observation_id='obs',target_component='component',proposed_mechanism='reported latency',expected_benefit='unknown',measurable_success_criteria='local test',falsification_criteria='no difference',assumptions=(),risk_class='LOW')
  self.p=r.make(r.ChangeProposal,proposal_id='proposal',hypothesis_id='hyp',change_type='TEST_PROPOSAL',target_component='component',target_version='v1',affected_interfaces=(),proposed_change_summary='test only',compatibility_requirements=(),prohibited_effects=r.DENIED,required_authorizations=('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',))
  self.risk=r.make(r.ImprovementRiskAssessment,proposal_id='proposal',regression_risks=(),security_risks=(),capability_boundary_risks=(),dependency_risks=(),rollback_requirements=(),unresolved_blockers=r.BLOCKERS)
  self.rp=r.make(r.ImprovementPolicy,policy_version='v1',permitted_proposal_types=r.TYPES,prohibited_operations=r.DENIED,evidence_requirements=('INDEPENDENT_PROVENANCE','ORIGINAL_ARTIFACTS'),risk_thresholds='LOW',resource_limits=16,required_approval_classes=('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',))
  self.inputs=(self.o,self.h,self.p,(self.e,),self.risk,self.rp,b.predecessor.initial(self.rp))
  self.policy=make(AssessmentPolicy,policy_version='v1',permitted_assessment_types=TYPES,evidence_requirements=('ORIGINAL_RSI001','NO_INDEPENDENT_CLAIM'),classification_rules='ordinal-v1',resource_limits=16,prohibited_operations=r.DENIED,inherited_blockers=BLOCKERS)
  self.s=make(ComponentSnapshot,component_id='component',component_version='v1',capability_ids=('cap',),interface_commitments=(),known_findings=BLOCKERS,evidence_refs=('e',))
  self.d=make(DependencyImpact,bottleneck_id='obs',upstream_dependencies=(),downstream_dependencies=(),affected_interfaces=(),possible_failure_modes=(),impact_class='DECLARED_NOT_VERIFIED',qualification_gaps=('PROVENANCE',))
  self.m=make(AssessmentMetric,metric_id='metric',component_id='component',metric_name='latency',value=10,unit='ms',measurement_context='synthetic',measurement_source='fixture',provenance_class='REPORTED_ONLY',qualification_status='DIAGNOSTIC')
  self.state=b.initial(self.policy)
 def remake(self,x,**kw):
  values={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};values.update(kw);return make(type(x),**values)
 def go(self,metrics=None,**kw):
  metrics=(self.m,) if metrics is None else metrics
  args=(self.s,metrics,'PERFORMANCE',self.d,self.inputs,self.policy,self.state)
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest((self.s,tuple(sorted(metrics,key=lambda x:x.metric_id)),'PERFORMANCE',self.d,self.inputs,self.policy)),sequence=self.state.sequence+1);controls.update(kw)
  return b.assess(*args,**controls)
 def test01_forged(self):
  with self.assertRaises(Exception): replace(self.m,commitment='0'*64)
 def test02_version(self):
  with self.assertRaises(Exception): self.remake(self.m,schema_version='bad')
 def test03_bool(self):
  with self.assertRaises(Exception): self.remake(self.m,value=True)
 def test04_identity(self):
  self.m=self.remake(self.m,component_id='other')
  with self.assertRaises(Exception): self.go()
 def test05_frozen(self):
  with self.assertRaises(Exception): self.m.value=2
 def test06_suspected(self): self.assertEqual(self.go()[3].assessment_status,'SUSPECTED')
 def test07_missing(self): self.assertEqual(self.go(metrics=())[3].assessment_status,'UNSUPPORTED')
 def test08_conflict(self): self.assertEqual(self.go(metrics=(self.m,self.remake(self.m,metric_id='other',measurement_source='other',value=20)))[3].assessment_status,'CONTRADICTED')
 def test09_no_gain(self): self.assertEqual(self.go()[1].observed_impact,'LOCAL_DIAGNOSTIC')
 def test10_categories(self): self.assertEqual(len(TYPES),9);self.assertIn(self.go()[1].bottleneck_type,TYPES)
 def test11_independence(self):
  with self.assertRaises(Exception): self.remake(self.m,provenance_class='INDEPENDENTLY_VERIFIED')
 def test12_duplicate(self):
  with self.assertRaises(Exception): self.go(metrics=(self.m,self.m))
 def test13_synthetic(self):
  with self.assertRaises(Exception): self.remake(self.m,qualification_status='VERIFIED')
 def test14_source_duplicate(self):
  with self.assertRaises(Exception): self.go(metrics=(self.m,self.remake(self.m,metric_id='other')))
 def test15_limits_preserved(self): self.assertIn('INDEPENDENT_PROVENANCE_UNAVAILABLE',self.go()[2][0].limitations)
 def test16_cycle(self):
  with self.assertRaises(Exception): self.remake(self.d,upstream_dependencies=('a',),downstream_dependencies=('a',))
 def test17_self_cycle(self):
  self.d=self.remake(self.d,upstream_dependencies=('component',))
  with self.assertRaises(Exception): self.go()
 def test18_priority(self):
  o=self.go()[1];other=self.remake(o,bottleneck_id='other');d=self.remake(self.d,bottleneck_id='other');a=((o,self.d,'LOW'),(other,d,'HIGH'));self.assertEqual(b.priority(a),b.priority(tuple(reversed(a))))
 def test19_order(self):
  m=self.remake(self.m,metric_id='other',measurement_source='other');self.assertEqual(self.go(metrics=(self.m,m)),self.go(metrics=(m,self.m)))
 def test20_findings(self):
  with self.assertRaises(Exception): self.remake(self.policy,inherited_blockers=())
 def test21_stop(self):
  with self.assertRaises(Exception): self.go(stop=True)
 def test22_deadline(self):
  with self.assertRaises(Exception): self.go(now=1,deadline=1)
 def test23_stale(self):
  with self.assertRaises(Exception): self.go(expected_state='0'*64)
 def test24_budget(self):
  self.policy=self.remake(self.policy,resource_limits=1);self.state=b.initial(self.policy)
  with self.assertRaises(Exception): self.go()
 def test25_replay(self):
  self.state=self.go()[0]
  with self.assertRaises(Exception): self.go()
 def test26_real_verdict(self): self.assertEqual(self.go()[3].evidence_qualification,'NOT_INDEPENDENTLY_QUALIFIED')
 def test27_actual_binding(self):
  self.inputs=(r.make(r.ImprovementObservation,**{**{f.name:getattr(self.o,f.name) for f in fields(self.o) if f.name!='commitment'},'source_commitment':'0'*64}),)+self.inputs[1:]
  with self.assertRaises(Exception): self.go()
 def test28_real_policy(self):
  values={f.name:getattr(self.p,f.name) for f in fields(self.p) if f.name!='commitment'};values['change_type']='SOURCE_REWRITE';self.inputs=self.inputs[:2]+(r.make(r.ChangeProposal,**values),)+self.inputs[3:]
  with self.assertRaises(Exception): self.go()
 def test29_flags(self): self.assertTrue(all(v is False for k,v in self.go()[3].authorization_flags))
 def test30_replay_determinism(self): self.assertEqual(self.go(),self.go())
if __name__=='__main__': unittest.main()
