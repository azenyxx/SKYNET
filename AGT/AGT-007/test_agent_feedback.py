import unittest
from dataclasses import replace
from unittest.mock import patch
import agent_feedback as f
import test_agent_planning as pf

class Tests(unittest.TestCase):
    def setUp(self):
        self.g,self.p,self.s,self.a,self.h=pf.fixture();self.r=f.planning.execute(self.g,self.p,self.s,self.a,self.h)
        self.policy=f.make(f.DecisionPolicy,policy_id='feedback',allowed_decisions=('ESCALATE','NO_ACTION'),max_proposals=8,resource_ceiling=32);self.prev=f.initial(self.g,self.policy)
        self.obs=f.observe(self.g,self.p,self.a,self.h,self.r);self.host=f.HostPins(self.g.goal_commitment,self.policy.policy_commitment,self.prev.state_commitment,(f.digest((self.g,self.p,self.a,self.h,self.r)),))
    def run_feedback(self,**kw):return f.evaluate(self.g,self.p,self.a,self.h,self.r,self.obs,self.policy,self.prev,self.host,**kw)
    def test01_real(self):self.assertEqual(len(self.run_feedback()[1]),5)
    def test02_replay(self):self.assertEqual(self.run_feedback(),self.run_feedback())
    def test03_confirmed(self):self.assertEqual(self.run_feedback()[2].consumed_budget,5)
    def test04_no_promotion(self):self.assertFalse(self.run_feedback()[-1].knowledge_promotion_authorized)
    def test05_false_verdict(self):self.assertRaises(ValueError,replace,self.run_feedback()[-1],verification_status='VERIFIED')
    def test06_source(self):self.host=replace(self.host,approved_sources=());self.assertRaises(ValueError,self.run_feedback)
    def test07_task(self):self.obs=(replace(self.obs[0],task_id='other',observation_commitment=self.obs[0].observation_commitment),)+self.obs[1:]
    def test08_stale(self):self.host=replace(self.host,expected_state='0'*64);self.assertRaises(ValueError,self.run_feedback)
    def test09_sequence(self):
        o=self.obs[0];kw={k.name:getattr(o,k.name) for k in f.fields(o) if k.name!='observation_commitment'};kw['observed_sequence']=2;self.obs=(f.make(f.ObservationRecord,**kw),)+self.obs[1:];self.assertRaises(ValueError,self.run_feedback)
    def test10_duplicate(self):
        self.prev=self.run_feedback()[0];self.host=replace(self.host,expected_state=self.prev.state_commitment);self.obs=f.observe(self.g,self.p,self.a,self.h,self.r,6);self.assertRaises(ValueError,self.run_feedback)
    def test11_stop(self):self.assertRaisesRegex(ValueError,'STOPPED',self.run_feedback,stop=True)
    def test12_deadline(self):self.assertRaisesRegex(ValueError,'DEADLINE',self.run_feedback,now=1,deadline=1)
    def test13_unchanged(self):before=f.digest(self.prev);self.assertRaises(ValueError,self.run_feedback,stop=True);self.assertEqual(before,f.digest(self.prev))
    def test14_failed(self):
        self.g,self.p,self.s,self.a,self.h=pf.fixture(bad=True);self.r=f.planning.execute(self.g,self.p,self.s,self.a,self.h);self.obs=f.observe(self.g,self.p,self.a,self.h,self.r);self.host=replace(self.host,approved_sources=(f.digest((self.g,self.p,self.a,self.h,self.r)),));out=self.run_feedback();self.assertEqual(out[-1].decision_status,'ESCALATE');self.assertEqual(out[2].blocked_task_ids,('B','C'));self.assertEqual(out[4][0].required_authorization,'TRUSTED_HOST_APPROVAL')
    def test15_uncertain(self):
        with patch.object(f.planning.gov.ar,'execute',side_effect=RuntimeError()):self.r=f.planning.execute(self.g,self.p,self.s,self.a,self.h)
        self.obs=f.observe(self.g,self.p,self.a,self.h,self.r);self.host=replace(self.host,approved_sources=(f.digest((self.g,self.p,self.a,self.h,self.r)),));out=self.run_feedback();self.assertEqual(out[2].uncertain_consumption,4);self.assertEqual(out[2].consumed_budget,0)
    def test16_production(self):self.assertRaises(ValueError,replace,self.run_feedback()[-1],production_authorized=True)
    def test17_version(self):self.assertRaises(ValueError,replace,self.policy,schema_version='bad')
    def test18_replan_guard(self):
        state=self.r[0];host=replace(self.h,expected_state=state.state_commitment);self.assertRaisesRegex(ValueError,'POST_EXECUTION',f.planning.revise,self.g,self.p,state,self.a,host,'FAILED_TASK')
if __name__=='__main__':unittest.main()
