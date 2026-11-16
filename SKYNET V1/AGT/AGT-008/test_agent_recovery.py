import unittest
from dataclasses import replace
from unittest.mock import patch
import agent_recovery as r
import test_agent_planning as pf
f=r.feedback

def fixture(uncertain=False):
    g,p,s,a,h=pf.fixture(bad=True)
    if uncertain:
        with patch.object(f.planning.gov.ar,'execute',side_effect=RuntimeError()):out=f.planning.execute(g,p,s,a,h)
    else:out=f.planning.execute(g,p,s,a,h)
    policy=f.make(f.DecisionPolicy,policy_id='feedback',allowed_decisions=('ESCALATE','NO_ACTION'),max_proposals=8,resource_ceiling=32);prev=f.initial(g,policy);obs=f.observe(g,p,a,h,out);pins=f.HostPins(g.goal_commitment,policy.policy_commitment,prev.state_commitment,(f.digest((g,p,a,h,out)),));src=(g,p,a,h,out,obs,policy,prev,pins)
    state=r.initial(src);rp=r.make(r.RecoveryPolicy,policy_id='recovery',allowed_operations=r.OPS,max_attempts=4,resource_ceiling=4)
    req=r.make(r.RecoveryRequest,request_id='request',goal_id=g.goal_id,plan_commitment=p.plan_commitment,source_state_commitment=out[0].state_commitment,reason_code='EXECUTION_UNCERTAIN' if uncertain else 'TASK_FAILED',requested_operations=('ESCALATE_TO_HOST',))
    c=r.make(r.RecoveryCandidate,candidate_id='candidate',request_id=req.request_id,affected_task_ids=('A',),proposed_operations=req.requested_operations,estimated_cost=1)
    auth=r.make(r.RecoveryAuthorization,authorization_id='approval',candidate_commitment=c.candidate_commitment,approved_operations=c.proposed_operations,approved_budget=1)
    host=r.HostPins(rp.policy_commitment,r.digest(src),state.state_commitment,(auth.authorization_commitment,))
    return [src,req,c,rp,auth,state,host]
class Tests(unittest.TestCase):
    def setUp(self):self.a=fixture()
    def run_case(self,**kw):return r.coordinate(*self.a,**kw)
    def test01_actual_chain(self):self.assertEqual(self.run_case()[2].execution_status,'COORDINATION_RECORDED')
    def test02_accounting(self):s=self.run_case()[0];self.assertEqual(s.consumed_budget+s.uncertain_consumption+s.reserved_capacity+s.remaining_budget,10)
    def test03_replay(self):self.assertEqual(self.run_case(),self.run_case())
    def test04_forged_auth(self):self.a[-1]=replace(self.a[-1],authorization_commitments=());self.assertRaises(ValueError,self.run_case)
    def test05_stale(self):self.a[-1]=replace(self.a[-1],expected_state='0'*64);self.assertRaisesRegex(ValueError,'STALE_STATE',self.run_case)
    def test06_duplicate(self):self.a[-2]=self.run_case()[0];self.a[-1]=replace(self.a[-1],expected_state=self.a[-2].state_commitment);self.assertRaisesRegex(ValueError,'DUPLICATE_REQUEST',self.run_case)
    def test07_stop(self):self.assertRaisesRegex(ValueError,'STOPPED',self.run_case,stop=True)
    def test08_deadline(self):self.assertRaisesRegex(ValueError,'DEADLINE',self.run_case,now=1,deadline=1)
    def test09_atomic(self):before=r.digest(self.a[-2]);self.assertRaises(ValueError,self.run_case,stop=True);self.assertEqual(before,r.digest(self.a[-2]))
    def test10_uncertain(self):self.a=fixture(True);s=self.run_case()[0];self.assertEqual((s.uncertain_consumption,s.consumed_budget),(4,1))
    def test11_production(self):self.assertRaises(ValueError,replace,self.run_case()[2],production_authorized=True)
    def test12_promotion(self):self.assertRaises(ValueError,replace,self.run_case()[2],knowledge_promotion_authorized=True)
    def test13_version(self):self.assertRaises(ValueError,replace,self.a[1],schema_version='bad')
    def test14_source_pin(self):self.a[-1]=replace(self.a[-1],source_commitment='0'*64);self.assertRaises(ValueError,self.run_case)
    def test15_commitment(self):self.assertRaises(ValueError,replace,self.a[2],candidate_commitment='0'*64)
    def change_operation(self,op):
        src,req,c,policy,auth,state,host=self.a
        req=r.make(r.RecoveryRequest,request_id=req.request_id,goal_id=req.goal_id,plan_commitment=req.plan_commitment,source_state_commitment=req.source_state_commitment,reason_code=req.reason_code,requested_operations=(op,));c=r.make(r.RecoveryCandidate,candidate_id=c.candidate_id,request_id=req.request_id,affected_task_ids=c.affected_task_ids,proposed_operations=(op,),estimated_cost=1);auth=r.make(r.RecoveryAuthorization,authorization_id='approval',candidate_commitment=c.candidate_commitment,approved_operations=(op,),approved_budget=1);self.a=[src,req,c,policy,auth,state,replace(host,authorization_commitments=(auth.authorization_commitment,))]
    def test16_replan_closed(self):self.change_operation('REQUEST_REPLAN');self.assertEqual(self.run_case()[1].feasibility_status,'NOT_QUALIFIED')
    def test17_reassign_closed(self):self.change_operation('REQUEST_REASSIGNMENT');self.assertEqual(self.run_case()[1].feasibility_status,'NOT_QUALIFIED')
    def test18_continue_closed(self):self.change_operation('CONTINUE_READY');self.assertEqual(self.run_case()[1].feasibility_status,'NOT_QUALIFIED')
    def test19_pause(self):self.change_operation('PAUSE_WORKFLOW');self.assertEqual(self.run_case()[1].feasibility_status,'ELIGIBLE')
    def test20_no_dispatch(self):
        with patch.object(f.planning.gov,'govern',side_effect=AssertionError('dispatch')),patch.object(f.planning,'execute',side_effect=AssertionError('dispatch')):self.run_case()
    def test21_unknown_task(self):
        old=self.a[2];self.a[2]=r.make(r.RecoveryCandidate,candidate_id=old.candidate_id,request_id=old.request_id,affected_task_ids=('missing',),proposed_operations=old.proposed_operations,estimated_cost=1);auth=r.make(r.RecoveryAuthorization,authorization_id='approval',candidate_commitment=self.a[2].candidate_commitment,approved_operations=old.proposed_operations,approved_budget=1);self.a[4]=auth;self.a[-1]=replace(self.a[-1],authorization_commitments=(auth.authorization_commitment,));self.assertRaisesRegex(ValueError,'UNKNOWN_TASK',self.run_case)
    def test22_bool(self):self.assertRaises(ValueError,replace,self.a[3],max_attempts=True)
    def test23_negative(self):self.assertRaises(ValueError,replace,self.a[3],resource_ceiling=-1)
    def test24_no_reconcile(self):self.a=fixture(True);before=self.a[-2].uncertain_consumption;self.assertEqual(self.run_case()[0].uncertain_consumption,before)
if __name__=='__main__':unittest.main()
