import unittest
from dataclasses import fields,replace,FrozenInstanceError
import continual_retention as r
import test_adaptive_learning as f

def change(v,**kw):
    d={x.name:getattr(v,x.name) for x in fields(v) if x.name!='commitment'}; d.update(kw); return r.make(type(v),**d)
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=f.Tests(); self.f.setUp(); self.load()
        self.x=r.make(r.CapabilitySnapshot,snapshot_id='before',metric_id='accuracy',unit='percent',direction='HIGHER',population=('task',),value=80,uncertainty=0,quality='DIAGNOSTIC',provenance=('fixture',))
        self.b=r.make(r.RetentionBaseline,baseline_id='baseline',snapshots=(self.x,),provenance=('fixture',))
        self.e=change(self.e,snapshots=(change(self.x,snapshot_id='after',value=82),))
        self.p=r.make(r.RetentionPolicy,policy_id='policy',tolerance=2,budget=32,max_cost=8,provenance=('host',)); self.state=r.initial(self.p)
    def load(self):
        out=self.f.invoke(); self.e=r.make(r.AdaptationEvidence,evaluation_id='evaluation',proposal=out[4][0],source=out[1],snapshots=(),provenance=('diagnostic',))
    def go(self,**kw):
        d=dict(expected_state=self.state.commitment,approved_input=r.digest((self.b,self.e,self.p)),sequence=self.state.sequence+1); d.update(kw); return r.evaluate(self.b,self.e,self.p,self.state,**d)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.x.value=3
    def test02_hash(self): self.bad(lambda:replace(self.x,commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.x,version='bad'))
    def test04_bool(self): self.bad(lambda:change(self.x,value=True))
    def test05_provenance(self): self.bad(lambda:change(self.x,provenance=['bad']))
    def test06_preserved(self): self.assertEqual(self.go()[1].status,'RETENTION_PRESERVED')
    def test07_regression(self):
        self.e=change(self.e,snapshots=(change(self.e.snapshots[0],value=70),)); self.assertEqual(self.go()[1].status,'REGRESSION_DETECTED')
    def test08_lower(self):
        self.b=change(self.b,snapshots=(change(self.x,direction='LOWER'),)); self.e=change(self.e,snapshots=(change(self.e.snapshots[0],direction='LOWER',value=70),)); self.assertEqual(self.go()[1].status,'RETENTION_PRESERVED')
    def test09_uncertainty(self):
        self.e=change(self.e,snapshots=(change(self.e.snapshots[0],uncertainty=10),)); self.assertEqual(self.go()[1].status,'INSUFFICIENT_EVIDENCE')
    def test10_missing(self):
        self.b=change(self.b,snapshots=()); self.e=change(self.e,snapshots=()); self.assertEqual(self.go()[1].status,'BASELINE_UNQUALIFIED')
    def test11_units(self):
        self.e=change(self.e,snapshots=(change(self.e.snapshots[0],unit='seconds'),)); self.bad(self.go)
    def test12_direction(self):
        self.e=change(self.e,snapshots=(change(self.e.snapshots[0],direction='LOWER'),)); self.bad(self.go)
    def test13_population(self):
        self.e=change(self.e,snapshots=(change(self.e.snapshots[0],population=('other',)),)); self.bad(self.go)
    def test14_baseline_provenance(self):
        self.b=change(self.b,provenance=()); self.assertEqual(self.go()[1].status,'BASELINE_UNQUALIFIED')
    def test15_repeated(self):
        self.e=change(self.e,snapshots=(self.x,)); self.bad(self.go)
    def test16_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test17_duplicate(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test18_budget(self):
        self.state=change(self.state,remaining=33); self.bad(self.go)
    def test19_sequence(self): self.bad(lambda:self.go(sequence=2))
    def test20_replay(self):
        a=self.go(); self.assertEqual(a,self.go()); self.assertEqual(a[0].consumed+a[0].remaining,32)
    def test21_stop(self): self.bad(lambda:self.go(stop=True))
    def test22_deadline(self): self.bad(lambda:self.go(now=1))
    def test23_model(self): self.bad(lambda:change(self.go()[2],model_update_authorized=True))
    def test24_knowledge(self): self.bad(lambda:change(self.go()[2],knowledge_promotion_authorized=True))
    def test25_production(self): self.bad(lambda:change(self.go()[2],production_authorized=True))
    def test26_actual_chain(self):
        self.f.sources=(f.fixtures.source(real=True),); self.load(); self.assertEqual(self.e.source.classifications,('PARTIALLY_VERIFIED',)); self.assertEqual(self.go()[1].status,'INSUFFICIENT_EVIDENCE')
    def test27_diagnostic(self):
        self.assertEqual(self.e.source.classifications,('REPORTED_ONLY',)); self.assertFalse(self.go()[2].learning_authorized)
    def test28_failed(self):
        self.f.sources=(f.fixtures.source(real=True,bad=True),); self.load(); self.assertEqual(self.e.source.outcomes,('FAILED',)); self.assertNotEqual(self.go()[1].status,'RETENTION_PRESERVED')
    def test29_missing_provenance(self):
        self.f.sources=(f.fixtures.source(provenance=''),); self.load(); self.assertEqual(self.go()[1].status,'NOT_QUALIFIED')
    def test30_duplicate_source(self):
        self.f.sources=(f.fixtures.source('a'),f.fixtures.source('b')); self.load(); self.assertEqual(self.e.source.source_diversity,1); self.assertEqual(self.go()[1].status,'INSUFFICIENT_EVIDENCE')
if __name__=='__main__': unittest.main()
