import unittest
from unittest.mock import patch
from dataclasses import replace,FrozenInstanceError
import agent_governance as gov
from agent_governance import *

def fixture(mode='CONTINUE_INDEPENDENT',budget=10,bad=False):
    policy=ExecutionPolicy('policy',mode,16,8,budget);identity=ac.AgentIdentity('agent','local',ac.OPS);tasks=[];bundles=[];grants=[];delegations=[]
    for k,deps in (('A',()),('B',('A',)),('C',('B',)),('E',()),('F',('E',))):
        t=ac.AgentTask(k,'agent','local',ac.digest('context','abc'),'grant:'+k,ac.OPS,4,4,2,100)
        a=(ac.AgentAction('action',k,'READ_CONTEXT',('bad' if bad and k=='A' else 'context',''),(),1,'READ_CONTEXT'),)
        g=ac.AuthorizationGrant(t.authorization_id,k,'agent',ac.digest('task',t),ac.digest('candidates',a),2);grants.append(g)
        d=DelegationGrant('delegate:'+k,'owner','agent',g.authorization_id,(k,),('READ_CONTEXT',),2,1);delegations.append(d)
        tasks.append(DelegatedTask(k,d.delegation_id,'agent',g.task_commitment,deps,2));bundles.append((identity,t,a,'abc',(g,),((False,0),)))
    host=HostAuthority('owner','request',digest(policy),tuple(digest(d) for d in delegations),tuple(grants),ac.OPS,('agent',))
    registry=(oc.SupervisedAgent('agent',oc.digest(identity),tuple(t.task_id for t in tasks)),)
    return ['request',policy,tuple(tasks),tuple(delegations),host,registry,tuple(bundles),tuple((False,i) for i in range(5)),100]
def run(**kw):return govern(*fixture(**kw))
def change_delegation(f,**kw):
    ds=(replace(f[3][0],**kw),)+f[3][1:];f[3]=ds;f[4]=replace(f[4],delegation_commitments=tuple(digest(d) for d in ds));return f
class Tests(unittest.TestCase):
    def bad(self,fn):self.assertRaises(ValueError,fn)
    def test01_frozen(self):self.assertRaises(FrozenInstanceError,setattr,fixture()[1],'max_tasks',1)
    def test02_version(self):self.bad(lambda:replace(fixture()[1],schema_version='bad'))
    def test03_negative(self):self.bad(lambda:replace(fixture()[1],global_budget=-1))
    def test04_bool(self):self.bad(lambda:replace(fixture()[1],global_budget=True))
    def test05_unknown_type(self):self.bad(lambda:digest(object()))
    def test06_keys(self):self.bad(lambda:digest({1:'x'}))
    def test07_forged_delegation(self):f=fixture();f[3]=(replace(f[3][0],max_budget=1),)+f[3][1:];self.bad(lambda:govern(*f))
    def test08_capability_escalation(self):f=fixture();f[4]=replace(f[4],parent_capabilities=());self.bad(lambda:govern(*f))
    def test09_budget_escalation(self):f=change_delegation(fixture(),max_budget=3);self.bad(lambda:govern(*f))
    def test10_cross_agent(self):f=change_delegation(fixture(),delegate_agent_id='other');self.bad(lambda:govern(*f))
    def test11_circular(self):self.bad(lambda:replace(fixture()[3][0],issuer_id='agent'))
    def test12_subdelegation(self):self.bad(lambda:replace(fixture()[3][0],delegation_depth=2))
    def test13_missing_parent(self):f=change_delegation(fixture(),parent_authorization_id='missing');self.bad(lambda:govern(*f))
    def test14_cycle(self):f=fixture();f[2]=(replace(f[2][0],dependencies=('C',)),)+f[2][1:];self.bad(lambda:govern(*f))
    def test15_missing_dependency(self):f=fixture();f[2]=(replace(f[2][0],dependencies=('unknown',)),)+f[2][1:];self.bad(lambda:govern(*f))
    def test16_continue(self):r=run(bad=True);self.assertEqual(r[0].completed_tasks,('E','F'))
    def test17_descendants(self):self.assertEqual(run(bad=True)[0].blocked_tasks,('B','C'))
    def test18_fail_stop(self):r=run(mode='FAIL_STOP',bad=True);self.assertEqual(r[0].completed_tasks,());self.assertEqual(len(r[3]),1)
    def test19_failed_visible(self):self.assertEqual(run(bad=True)[0].failed_tasks,('A',))
    def test20_policy_bound(self):f=fixture();f[1]=replace(f[1],failure_mode='FAIL_STOP');self.bad(lambda:govern(*f))
    def test21_conservation(self):r=run();s=r[0];self.assertEqual(s.confirmed_spend+s.reserved_capacity+s.uncertain_spend+s.remaining_available_budget,10)
    def test22_reserve_before(self):r=run();self.assertEqual(r[1].accounting_events[0],('A','RESERVE',0,2,0,8))
    def test23_exception_uncertain(self):
        with patch.object(ar,'execute',side_effect=RuntimeError('private')):r=run()
        self.assertEqual((r[0].confirmed_spend,r[0].uncertain_spend),(0,4));self.assertNotIn('private',str(r))
    def test24_uncertain_no_reuse(self):
        with patch.object(ar,'execute',side_effect=RuntimeError()) as p:r=run(budget=2)
        self.assertEqual(p.call_count,1);self.assertEqual((r[0].uncertain_spend,r[0].remaining_available_budget),(2,0))
    def test25_duplicate(self):f=fixture();f[2]=(f[2][0],)*5;self.bad(lambda:govern(*f))
    def test26_negative_available(self):self.bad(lambda:replace(run()[0],remaining_available_budget=-1))
    def test27_account_invariant(self):self.bad(lambda:replace(run()[0],confirmed_spend=0))
    def test28_real_execution(self):self.assertEqual(len(run()[3]),5)
    def test29_original_verdict(self):r=run();self.assertEqual(r[3][0][1][2].execution_status,'COMPLETED')
    def test30_local_check(self):self.assertEqual(run()[1].task_outcomes[0].semantic_status,'LOCAL_REEXECUTION_CHECK')
    def test31_forged_trace(self):
        f=fixture();b=f[6][0];p=ar.plan(b[1],b[2]);r=ar.execute(*b);self.bad(lambda:qualify_output(b,p,(r[0],replace(r[1],trace_commitment='0'*64),r[2])))
    def test32_output_mismatch(self):
        b=fixture()[6][0];p=ar.plan(b[1],b[2]);s,t,v=ar.execute(*b);o=t.observations[0];ocm=ac.digest('output','forged');oid='o:'+ac.digest('observation',('A','action',o.input_commitment,ocm,True));o=replace(o,output_commitment=ocm,observation_id=oid,evidence_refs=(oid,));tc=ac.digest('trace',('A',t.ordered_events,(o,)));t=replace(t,observations=(o,),trace_commitment=tc,trace_id='t:'+tc);s=replace(s,last_observation_id=oid);self.bad(lambda:qualify_output(b,p,(s,t,v)))
    def test33_stop_before(self):f=fixture();f[7]=tuple((True,i) for i in range(5));r=govern(*f);self.assertEqual((r[0].status,len(r[3])),('STOPPED',0))
    def test34_stop_partial(self):f=fixture();f[7]=((False,0),)+tuple((True,i) for i in range(1,5));r=govern(*f);self.assertEqual((r[0].status,len(r[3])),('STOPPED',1))
    def test35_deadline(self):f=fixture();f[8]=0;self.assertEqual(govern(*f)[0].status,'DEADLINE')
    def test36_retry(self):self.bad(lambda:replace(fixture()[1],retry_limit=1))
    def test37_replay(self):self.assertTrue(replay_equal(run(),run()))
    def test38_changed_policy(self):self.assertFalse(replay_equal(run(),run(mode='FAIL_STOP')))
    def test39_trust(self):self.assertEqual(run()[2].verification_status,'NOT_ESTABLISHED');self.bad(lambda:replace(run()[2],knowledge_promotion_authorized=True))
    def test40_production(self):self.bad(lambda:replace(run()[2],production_authorized=True))
if __name__=='__main__':unittest.main()
