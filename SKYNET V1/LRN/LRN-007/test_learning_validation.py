import unittest
from dataclasses import fields,replace,FrozenInstanceError
import learning_validation as v
import test_meta_learning as f
def change(obj,**kw):
    d={x.name:getattr(obj,x.name) for x in fields(obj) if x.name!='commitment'}; d.update(kw); return v.make(type(obj),**d)
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=f.Tests(); self.f.setUp(); self.load()
        self.policy=v.make(v.ValidationPolicy,policy_id='validation',budget=16,max_cost=8,allowed_adjustments=v.m.KINDS,provenance=('host',)); self.state=v.initial(self.policy)
    def load(self):
        result=self.f.go(); self.chain=v.make(v.EvidenceChain,request_id='request',context=self.f.context,entries=self.f.entries,policy=self.f.policy,previous=self.f.state,result=result,provenance=('fixture',))
        self.candidate=v.make(v.ValidationCandidate,candidate_id='candidate',strategy_id=result[2][0].strategy_id,chain_commitment=self.chain.commitment,proposal=result[2][0],provenance=('fixture',))
    def go(self,**kw):
        args=dict(expected_state=self.state.commitment,approved_input=v.digest((self.candidate,self.chain,self.policy)),sequence=self.state.sequence+1); args.update(kw); return v.validate(self.candidate,self.chain,self.policy,self.state,**args)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.policy.budget=1
    def test02_hash(self): self.bad(lambda:replace(self.policy,commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.policy,version='bad'))
    def test04_bool(self): self.bad(lambda:change(self.policy,budget=True))
    def test05_identifier(self): self.bad(lambda:change(self.candidate,candidate_id='bad id'))
    def test06_chain(self):
        self.candidate=change(self.candidate,chain_commitment='0'*64); self.bad(self.go)
    def test07_identity(self): self.bad(lambda:change(self.candidate,strategy_id='wrong'))
    def test08_meta_result(self):
        state=f.change(self.chain.result[0],remaining=self.chain.result[0].remaining+1)
        self.chain=change(self.chain,result=(state,)+self.chain.result[1:]); self.candidate=change(self.candidate,chain_commitment=self.chain.commitment); self.bad(self.go)
    def test09_proposal(self):
        self.candidate=change(self.candidate,proposal=f.change(self.candidate.proposal,expected_cost=7)); self.bad(self.go)
    def test10_classes(self): self.assertEqual(self.go()[1].provenance_assessment.original_classes,('REPORTED_ONLY',))
    def test11_independent(self): self.bad(lambda:change(self.go()[1].provenance_assessment,classification='INDEPENDENTLY_VERIFIED'))
    def test12_originals(self): self.assertIn('LRN001_ORIGINALS',self.go()[1].provenance_assessment.missing)
    def test13_dup_provenance(self): self.bad(lambda:change(self.chain,provenance=('same','same')))
    def test14_unqualified(self): self.assertEqual(self.go()[1].provenance_assessment.qualification,'NOT_QUALIFIED')
    def test15_synthetic(self): self.assertNotEqual(self.go()[2].status,'QUALIFIED_FOR_FURTHER_VALIDATION')
    def test16_regression_gate(self): self.assertEqual(self.go()[1].regression.status,'REGRESSION_GATE_PASSED')
    def test17_target(self): self.assertIn('TARGET_MEASUREMENTS_MISSING',self.go()[1].reasons)
    def test18_transfer(self): self.assertIn('TRANSFER_NOT_QUALIFIED',self.go()[1].reasons)
    def test19_policy(self):
        self.policy=change(self.policy,allowed_adjustments=()); self.state=v.initial(self.policy); self.assertEqual(self.go()[2].status,'POLICY_BLOCKED')
    def test20_blockers(self): self.assertIn('A09-001',self.go()[1].blockers); self.assertIn('L06-001',self.go()[1].blockers)
    def test21_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test22_budget(self):
        self.state=change(self.state,remaining=17); self.bad(self.go)
    def test23_stop_deadline(self): self.bad(lambda:self.go(stop=True)); self.bad(lambda:self.go(now=1))
    def test24_duplicate(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test25_flags(self):
        verdict=self.go()[2]
        for name in ('learning_authorized','model_update_authorized','knowledge_promotion_authorized','production_authorized','strategy_change_authorized','policy_change_authorized'): self.bad(lambda:change(verdict,**{name:True}))
    def test26_real_chain(self):
        self.f.entries=(self.f.entry('a',90,real=True),self.f.entry('b',70,real=True)); self.load(); self.assertEqual(self.go()[1].provenance_assessment.original_classes,('PARTIALLY_VERIFIED',))
    def test27_real_failed_excluded(self):
        self.f.entries=(self.f.entry('a',90,real=True,bad=True),self.f.entries[1]); result=self.f.go(); self.assertIn('REGRESSION_RISK',[x.status for x in result[1]]); self.assertFalse(any(x.strategy_id=='a' for x in result[2]))
    def test28_real_proposal(self): self.assertEqual(self.candidate.proposal,self.chain.result[2][0]); self.assertEqual(self.go()[2].status,'INTEGRATION_NOT_QUALIFIED')
    def test29_real_recompute(self): self.assertEqual(self.go(),self.go()); self.assertEqual(self.go()[0].consumed+self.go()[0].remaining,16)
    def test30_real_retention(self): self.assertEqual(self.go()[1].regression.retention_commitment,self.chain.entries[0][0].evidence.retention.commitment)
if __name__=='__main__': unittest.main()
