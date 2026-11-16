import unittest
from dataclasses import fields,replace,FrozenInstanceError
import integrated_qualification as q
import test_learning_validation as f
def change(v,**kw):
    d={x.name:getattr(v,x.name) for x in fields(v) if x.name!='commitment'}; d.update(kw); return q.make(type(v),**d)
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=f.Tests(); self.f.setUp(); self.state=q.initial(); self.findings=q.make(q.FindingRegister,entries=q.FINDINGS,provenance=('OWNER_SPECIFICATION',))
        self.stages=tuple(q.make(q.StageQualification,stage_id=s,reported_status='CLOSED PARTIAL',artifact_status='UNAVAILABLE',artifact_commitment='0'*64,test_status='REPORTED',reproduction='NOT_QUALIFIED',integration='NOT_QUALIFIED',synthetic=True,open_findings=tuple(x[0] for x in q.FINDINGS if x[2]==s),unqualified=('INDEPENDENT_PROVENANCE',),provenance=('OWNER_REPORTED',)) for s in q.STAGES)
    def go(self,**kw):
        inputs=(self.f.candidate,self.f.chain,self.f.policy,self.f.state); options=dict(expected_state=self.state.commitment,approved_input=q.digest(('audit',self.stages,self.findings,inputs)),sequence=self.state.sequence+1); options.update(kw); return q.qualify('audit',self.stages,self.findings,inputs,self.state,**options)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.state.remaining=9
    def test02_hash(self): self.bad(lambda:replace(self.state,commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.state,version='bad'))
    def test04_boolean(self): self.bad(lambda:change(self.state,consumed=True))
    def test05_independence(self): self.bad(lambda:change(self.stages[0],reproduction='INDEPENDENTLY_VERIFIED'))
    def test06_eight(self): self.assertEqual(len(self.go()[1][0]),8)
    def test07_missing(self): self.assertIn('LRN-001',self.go()[1][1].missing)
    def test08_duplicates(self):
        self.stages=self.stages[:-1]+(self.stages[0],); self.bad(self.go)
    def test09_reported(self): self.assertEqual(self.go()[1][0][0].test_status,'REPORTED')
    def test10_incomplete(self):
        self.stages=self.stages[:-1]; self.bad(self.go)
    def test11_broken(self):
        self.f.candidate=f.change(self.f.candidate,chain_commitment='0'*64); self.bad(self.go)
    def test12_originals(self): self.assertIn('LRN001_ORIGINALS',self.go()[1][1].missing)
    def test13_synthetic(self): self.assertTrue(self.go()[1][2].synthetic)
    def test14_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test15_replay(self): self.assertEqual(self.go(),self.go())
    def test16_count(self): self.assertEqual(len(self.go()[1][3].entries),23)
    def test17_p1(self): self.assertEqual(sum(x[1]=='P1' for x in self.findings.entries),9)
    def test18_suppress(self): self.bad(lambda:change(self.findings,entries=q.FINDINGS[1:]))
    def test19_close(self):
        entry=q.FINDINGS[0]; self.bad(lambda:change(self.findings,entries=(entry[:3]+('CLOSED',)+entry[4:],)+q.FINDINGS[1:]))
    def test20_priorities(self): self.assertEqual(self.go()[1][5].priorities,q.PRIORITIES)
    def test21_authorizations(self):
        verdict=self.go()[2]
        for flag in q.FLAGS: self.bad(lambda:change(verdict,**{flag:True}))
    def test22_budget(self): self.bad(lambda:change(self.state,remaining=33))
    def test23_stop(self): self.bad(lambda:self.go(stop=True)); self.bad(lambda:self.go(now=1))
    def test24_duplicate(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test25_not_established(self): self.assertIn('FULL_PER_STAGE_RUNTIME_AUDIT',self.go()[1][4].not_established)
    def test26_actual_chain(self):
        self.f.f.entries=(self.f.f.entry('a',90,real=True),self.f.f.entry('b',70,real=True)); self.f.load(); self.assertEqual(self.go()[2].status,'CLOSED PARTIAL')
    def test27_actual_validation(self): self.assertEqual(self.f.go()[2].status,'INTEGRATION_NOT_QUALIFIED'); self.assertEqual(self.go()[1][2].executed,('LRN-004','LRN-006','LRN-007'))
    def test28_actual_flags(self): self.assertEqual(self.go()[1][4].checked,q.FLAGS)
    def test29_actual_failed(self):
        x=self.f.f; x.entries=(x.entry('a',90,real=True,bad=True),x.entries[1]); result=x.go(); self.assertIn('REGRESSION_RISK',[a.status for a in result[1]]); self.assertFalse(any(a.strategy_id=='a' for a in result[2]))
    def test30_actual_readiness(self): self.assertIn('BLOCKED_BY_CRITICAL_FINDINGS',self.go()[1][5].dimensions); self.assertIn('EVIDENCE_NOT_QUALIFIED',self.go()[1][5].dimensions)
if __name__=='__main__': unittest.main()
