import unittest
from dataclasses import fields,replace,FrozenInstanceError
import meta_learning as m
import test_transfer_evaluation as f
def change(v,**kw):
    d={x.name:getattr(v,x.name) for x in fields(v) if x.name!='commitment'}; d.update(kw); return m.make(type(v),**d)
class Tests(unittest.TestCase):
    def setUp(self):
        self.context=m.make(m.MetaLearningContext,context_id='context',target_id='target',task_category='classification',metric_id='accuracy',unit='percent',direction='HIGHER',population=('task',),provenance=('fixture',))
        self.policy=m.make(m.MetaLearningPolicy,policy_id='meta',existing_policy_commitment='a'*64,budget=16,max_declared_cost=8,proposal_kind='STRATEGY_SELECTION_CHANGE',provenance=('host',)); self.state=m.initial(self.policy)
        self.entries=(self.entry('a',90),self.entry('b',70))
    def entry(self,name,value,real=False,bad=False):
        x=f.Tests(); x.setUp()
        upstream=x.f.f
        upstream.candidates=(f.f.f.changed(upstream.candidates[0],strategy_id=name),)
        if real: upstream.sources=(f.f.f.fixtures.source(real=True,bad=bad),)
        x.f.load()
        x.f.e=f.f.change(x.f.e,snapshots=(f.f.change(x.f.x,snapshot_id='after-'+name,value=82),))
        x.load(); result=x.go()
        h=m.make(m.StrategyHistory,strategy_id=name,category='EVIDENCE_FILTERING',source=x.s,target=x.target,evidence=x.e,assessment=result[1],candidate=result[2],verdict=result[3],provenance=('fixture',))
        obs=f.f.change(x.f.x,snapshot_id='measured-'+name,value=value)
        p=m.make(m.StrategyPerformanceEvidence,evidence_id='performance-'+name,history_commitment=h.commitment,context_commitment=self.context.commitment,observations=(obs,),provenance=('synthetic',))
        return h,p
    def go(self,**kw):
        opts=dict(expected_state=self.state.commitment,approved_input=m.digest(('request',self.context,self.entries,self.policy)),sequence=self.state.sequence+1); opts.update(kw); return m.evaluate('request',self.context,self.entries,self.policy,self.state,**opts)
    def bad(self,fn):
        with self.assertRaises(ValueError): fn()
    def editp(self,**kw): self.entries=((self.entries[0][0],change(self.entries[0][1],**kw)),self.entries[1])
    def test01_frozen(self):
        with self.assertRaises(FrozenInstanceError): self.policy.budget=3
    def test02_hash(self): self.bad(lambda:replace(self.policy,commitment='0'*64))
    def test03_version(self): self.bad(lambda:change(self.policy,version='bad'))
    def test04_bool(self): self.bad(lambda:change(self.policy,budget=True))
    def test05_direction(self): self.bad(lambda:change(self.context,direction='UP'))
    def test06_history_binding(self):
        h,p=self.entries[0]; self.bad(lambda:change(h,candidate=f.change(h.candidate,evidence_commitment='0'*64)))
    def test07_metric(self):
        self.editp(observations=(f.f.change(self.entries[0][1].observations[0],unit='seconds'),)); self.bad(self.go)
    def test08_missing(self):
        self.editp(observations=()); self.assertEqual({x.status for x in self.go()[1]},{'INSUFFICIENT_EVIDENCE'})
    def test09_provenance(self):
        self.editp(provenance=()); self.assertEqual(self.go()[1][0].status,'INSUFFICIENT_EVIDENCE')
    def test10_duplicates(self):
        self.editp(observations=self.entries[1][1].observations); self.bad(self.go)
    def test11_winner(self): self.assertEqual(self.go()[1][0].strategy_id,'a'); self.assertEqual(self.go()[1][0].status,'PREFERRED_FOR_VALIDATION')
    def test12_tie(self):
        self.entries=(self.entry('a',70),self.entry('b',70)); self.assertEqual({x.status for x in self.go()[1]},{'COMPARABLE_NO_WINNER'})
    def test13_uncertainty(self):
        self.editp(observations=(f.f.change(self.entries[0][1].observations[0],uncertainty=40),)); self.assertEqual(self.go()[1][0].status,'COMPARABLE_NO_WINNER')
    def test14_replay(self): self.assertEqual(self.go(),self.go())
    def test15_order(self):
        a=self.go()[1]; self.entries=self.entries[::-1]; self.assertEqual(a,self.go()[1])
    def test16_proposal(self): self.assertEqual(self.go()[2][0].adjustment,'STRATEGY_SELECTION_CHANGE')
    def test17_threshold(self):
        self.policy=change(self.policy,proposal_kind='EVIDENCE_THRESHOLD_CHANGE'); self.state=m.initial(self.policy); self.assertIn('NO_THRESHOLD_RELAXATION',self.go()[2][0].required_validation)
    def test18_schedule(self):
        self.policy=change(self.policy,proposal_kind='EVALUATION_SCHEDULE_CHANGE'); self.state=m.initial(self.policy); self.assertEqual(self.go()[2][0].adjustment,self.policy.proposal_kind)
    def test19_allocation(self):
        self.policy=change(self.policy,proposal_kind='REPLAY_ALLOCATION_CHANGE'); self.state=m.initial(self.policy); self.assertEqual(self.go()[2][0].adjustment,self.policy.proposal_kind)
    def test20_flags(self):
        v=self.go()[3]
        for flag in ('strategy_change_authorized','policy_change_authorized','model_update_authorized','production_authorized','learning_authorized','knowledge_promotion_authorized'): self.bad(lambda:change(v,**{flag:True}))
    def test21_stale(self): self.bad(lambda:self.go(expected_state='0'*64))
    def test22_budget(self):
        self.state=change(self.state,remaining=17); self.bad(self.go)
    def test23_stop(self): self.bad(lambda:self.go(stop=True))
    def test24_deadline(self): self.bad(lambda:self.go(now=1))
    def test25_duplicate_request(self):
        self.state=self.go()[0]; self.bad(self.go)
    def test26_real_chain(self):
        self.entries=(self.entry('a',90,real=True),self.entry('b',70,real=True)); self.assertEqual(self.entries[0][0].evidence.adaptation.source.classifications,('PARTIALLY_VERIFIED',)); self.assertTrue(self.go()[2])
    def test27_failed(self):
        self.entries=(self.entry('a',90,real=True,bad=True),self.entries[1]); self.assertIn('REGRESSION_RISK',[x.status for x in self.go()[1]])
    def test28_retention(self): self.assertEqual(self.entries[0][0].evidence.retention.status,'RETENTION_PRESERVED'); self.assertTrue(self.go()[1])
    def test29_transfer(self): self.assertEqual(self.entries[0][0].verdict.status,'NOT_QUALIFIED'); self.assertEqual(self.go()[3].status,'ADVISORY_NOT_QUALIFIED')
    def test30_trust(self): self.assertEqual(self.entries[0][0].evidence.adaptation.source.classifications,('REPORTED_ONLY',)); self.assertIn('INDEPENDENT_PROVENANCE_NOT_ESTABLISHED',self.go()[1][0].reasons)
if __name__=='__main__': unittest.main()
