import unittest
from dataclasses import fields,replace,FrozenInstanceError
import self_improvement_foundation as r
import test_integrated_qualification as fixture
def change(x,**kw):
    d={f.name:getattr(x,f.name) for f in fields(x) if f.name!=r.seal(type(x))}; d.update(kw); return r.make(type(x),**d)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=fixture.Tests(); f.setUp(); cls.lrn=f.go()
    def setUp(self):
        self.e=(r.consume_lrn(self.lrn),)
        self.o=r.make(r.ImprovementObservation,observation_id='obs',component_id='LRN-008',component_version='v1',observation_type='DEFICIENCY',evidence_refs=(self.e[0].evidence_id,),observed_metrics=(),confidence=(0,1),provenance_class='STRUCTURALLY_BOUND',source_commitment=r.digest(self.e))
        self.h=r.make(r.ImprovementHypothesis,hypothesis_id='hyp',observation_id='obs',target_component='LRN-008',proposed_mechanism='Add externally reviewed evidence validation',expected_benefit='Hypothesis only: fewer unsupported claims',measurable_success_criteria='Reject all forged evidence fixtures',falsification_criteria='Any forged fixture accepted',assumptions=('ORIGINALS_AVAILABLE',),risk_class='LOW')
        self.p=r.make(r.ChangeProposal,proposal_id='proposal',hypothesis_id='hyp',change_type='TEST_PROPOSAL',target_component='LRN-008',target_version='v1',affected_interfaces=('qualification',),proposed_change_summary='Propose adversarial tests only',compatibility_requirements=('NO_AUTHORITY_CHANGE',),prohibited_effects=r.DENIED,required_authorizations=('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',))
        self.risk=r.make(r.ImprovementRiskAssessment,proposal_id='proposal',regression_risks=('COVERAGE_UNKNOWN',),security_risks=(),capability_boundary_risks=('PROVENANCE',),dependency_risks=('ORIGINALS',),rollback_requirements=('NO_ACTIVATION',),unresolved_blockers=r.BLOCKERS)
        self.policy=r.make(r.ImprovementPolicy,policy_version='v1',permitted_proposal_types=r.TYPES,prohibited_operations=r.DENIED,evidence_requirements=('INDEPENDENT_PROVENANCE','ORIGINAL_ARTIFACTS'),risk_thresholds='LOW',resource_limits=8,required_approval_classes=('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',)); self.state=r.initial(self.policy)
    def go(self,**kw):
        d=dict(expected_state=self.state.state_commitment,approved_input=r.digest((self.o,self.h,self.p,self.e,self.risk,self.policy,self.lrn)),sequence=self.state.sequence+1,lrn_result=self.lrn); d.update(kw); return r.assess(self.o,self.h,self.p,self.e,self.risk,self.policy,self.state,**d)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.o.confidence=(1,1)
    def test02_forged(self): self.bad(lambda:replace(self.e[0],commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.p,schema_version='bad'))
    def test04_boolean(self): self.bad(lambda:change(self.policy,resource_limits=True))
    def test05_canonical(self): self.assertEqual(r.digest(self.e),r.digest(tuple(self.e)))
    def test06_lifecycle(self): self.assertEqual(self.go()[1],r.LIFECYCLE)
    def test07_binding(self):
        self.p=change(self.p,hypothesis_id='wrong'); self.bad(self.go)
    def test08_target(self):
        self.p=change(self.p,target_version='v2'); self.bad(self.go)
    def test09_no_gain(self): self.assertEqual(self.go()[2].decision,'INTEGRATION_NOT_QUALIFIED')
    def test10_determinism(self): self.assertEqual(self.go(),self.go())
    def test11_independent(self): self.bad(lambda:change(self.e[0],provenance_class='INDEPENDENTLY_VERIFIED'))
    def test12_synthetic(self): self.bad(lambda:change(self.e[0],verification_status='VERIFIED'))
    def test13_duplicate_evidence(self):
        self.e=self.e*2; self.bad(self.go)
    def test14_missing(self):
        self.e=(); self.o=change(self.o,evidence_refs=()); self.lrn=None; self.assertEqual(self.go()[2].decision,'REQUIRES_EVIDENCE')
    def test15_contradiction(self):
        self.o=change(self.o,provenance_class='CONTRADICTED'); self.assertEqual(self.go()[2].decision,'REJECTED')
    def test16_p1(self): self.bad(lambda:change(self.risk,unresolved_blockers=r.BLOCKERS[1:]))
    def test17_relaxation(self): self.bad(lambda:change(self.policy,evidence_requirements=()))
    def test18_self_authority(self):
        v=self.go()[2]; self.bad(lambda:change(v,authorization_flags=tuple((n,True) for n in r.FLAGS)))
    def test19_code(self):
        self.p=change(self.p,change_type='SOURCE_REWRITE'); self.assertEqual(self.go()[2].decision,'POLICY_BLOCKED')
    def test20_risk(self):
        self.h=change(self.h,risk_class='HIGH'); self.assertEqual(self.go()[2].decision,'RISK_BLOCKED')
    def test21_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test22_duplicate(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test23_budget(self):
        self.policy=change(self.policy,resource_limits=1); self.state=r.initial(self.policy); self.bad(self.go)
    def test24_stop(self): self.bad(lambda:self.go(stop=True))
    def test25_deadline(self): self.bad(lambda:self.go(now=1))
    def test26_lrn_adapter(self): self.assertEqual(self.e[0].source_commitment,r.digest(self.lrn)); self.assertEqual(self.go()[2].evidence_qualification,'NOT_QUALIFIED')
    def test27_lrn_partial(self): self.assertEqual(self.lrn[2].status,'CLOSED PARTIAL'); self.assertIn('LRN_CLOSED_PARTIAL',self.go()[2].decision_reasons)
    def test28_findings(self): self.assertEqual(len(r.FINDINGS),26); self.assertEqual(sum(x[1]=='P1' for x in r.FINDINGS),10)
    def test29_lrn_safety(self): self.assertTrue(all(getattr(self.lrn[2],n) is False for n in r.q.FLAGS)); self.assertTrue(all(x is False for _,x in self.go()[2].authorization_flags))
    def test30_lrn_missing(self): self.assertIn('LRN001_ORIGINALS',self.lrn[1][1].missing); self.assertIn('A09-001',self.go()[2].unresolved_findings)
if __name__=='__main__': unittest.main()
