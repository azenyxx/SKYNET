import unittest
from dataclasses import fields,replace,FrozenInstanceError
import transfer_evaluation as t
import test_continual_retention as f
def change(v,**kw):
    d={x.name:getattr(v,x.name) for x in fields(v) if x.name!='commitment'}; d.update(kw); return t.make(type(v),**d)
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=f.Tests(); self.f.setUp(); self.load()
        common=dict(task_category='classification',capabilities=('classify',),input_schema='text',output_schema='label',metric_id='accuracy',unit='percent',direction='HIGHER',constraints=('offline',),failures=(),provenance=('fixture',))
        self.s=t.make(t.SourceDomainProfile,domain_id='source',**common); self.target=t.make(t.TargetDomainProfile,domain_id='target',**common)
        self.p=t.make(t.TransferPolicy,policy_id='policy',source_id='source',target_id='target',allowed_constraints=('offline','local'),budget=8,provenance=('host',)); self.state=t.initial(self.p)
    def load(self):
        result=self.f.go(); self.e=t.make(t.TransferEvidence,request_id='request',source_id='source',target_id='target',adaptation=self.f.e,baseline=self.f.b,retention_policy=self.f.p,retention=result[1],target_measurements=(),provenance=('fixture',))
    def go(self,**kw):
        d=dict(expected_state=self.state.commitment,approved_input=t.digest((self.s,self.target,self.e,self.p)),sequence=self.state.sequence+1); d.update(kw); return t.evaluate(self.s,self.target,self.e,self.p,self.state,**d)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.s.domain_id='bad'
    def test02_hash(self): self.bad(lambda:replace(self.s,commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.s,version='bad'))
    def test04_boolean_budget(self): self.bad(lambda:change(self.p,budget=True))
    def test05_binding(self):
        self.e=change(self.e,target_id='wrong'); self.bad(self.go)
    def test06_compatible(self): self.assertEqual(self.go()[1].status,'COMPATIBLE_FOR_EVALUATION')
    def test07_task(self):
        self.target=change(self.target,task_category='other'); self.assertEqual(self.go()[2].status,'REJECTED')
    def test08_schema(self):
        self.target=change(self.target,input_schema='image'); self.assertIn('SCHEMA_MISMATCH',self.go()[2].reasons)
    def test09_units(self):
        self.target=change(self.target,unit='seconds'); self.assertEqual(self.go()[2].status,'REJECTED')
    def test10_direction(self):
        self.target=change(self.target,direction='LOWER'); self.assertEqual(self.go()[2].status,'REJECTED')
    def test11_missing_target(self): self.assertEqual(self.go()[3].status,'NOT_QUALIFIED')
    def test12_no_promotion(self): self.assertEqual(self.go()[2].trust_distribution,(('REPORTED_ONLY',1),))
    def test13_provenance(self):
        self.target=change(self.target,provenance=()); self.assertIn('PROVENANCE_UNRESOLVED',self.go()[2].reasons)
    def test14_constraints(self):
        self.target=change(self.target,constraints=('network',)); self.bad(self.go)
    def test15_model_flag(self): self.bad(lambda:change(self.go()[3],model_update_authorized=True))
    def test16_coverage(self):
        self.target=change(self.target,capabilities=('classify','invent')); self.assertEqual(self.go()[1].unsupported,('invent',))
    def test17_failure(self):
        self.s=change(self.s,failures=('known',)); self.assertEqual(self.go()[2].status,'NEGATIVE_TRANSFER_RISK')
    def test18_constraints_conflict(self):
        self.target=change(self.target,constraints=('local',)); self.assertEqual(self.go()[2].status,'REJECTED')
    def test19_empty(self):
        self.target=change(self.target,capabilities=()); self.assertEqual(self.go()[1].status,'INSUFFICIENT_EVIDENCE')
    def test20_determinism(self): self.assertEqual(self.go(),self.go())
    def test21_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test22_budget(self):
        self.state=change(self.state,remaining=9); self.bad(self.go)
    def test23_stop_deadline(self):
        self.bad(lambda:self.go(stop=True)); self.bad(lambda:self.go(now=1))
    def test24_duplicate(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test25_authority(self):
        v=self.go()[3]; self.bad(lambda:change(v,production_authorized=True)); self.assertFalse(v.learning_authorized or v.knowledge_promotion_authorized)
    def test26_real_chain(self):
        self.f.f.sources=(f.f.fixtures.source(real=True),); self.f.load(); self.load(); self.assertEqual(self.go()[2].trust_distribution,(('PARTIALLY_VERIFIED',1),))
    def test27_real_regression(self):
        self.f.e=f.change(self.f.e,snapshots=(f.change(self.f.e.snapshots[0],value=60),)); self.load(); self.assertEqual(self.go()[2].status,'NEGATIVE_TRANSFER_RISK')
    def test28_real_failed(self):
        self.f.f.sources=(f.f.fixtures.source(real=True,bad=True),); self.f.load(); self.load(); self.assertEqual(self.go()[2].status,'NEGATIVE_TRANSFER_RISK')
    def test29_real_missing(self):
        self.f.f.sources=(f.f.fixtures.source(provenance=''),); self.f.load(); self.load(); self.assertEqual(self.go()[2].status,'NOT_QUALIFIED')
    def test30_real_dedup(self):
        self.f.f.sources=(f.f.fixtures.source('a'),f.f.fixtures.source('b')); self.f.load(); self.load(); self.assertEqual(self.go()[2].trust_distribution,(('REPORTED_ONLY',1),)); self.assertEqual(self.go()[3].status,'NOT_QUALIFIED')
if __name__=='__main__': unittest.main()
