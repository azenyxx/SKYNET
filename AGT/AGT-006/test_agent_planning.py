import unittest
from unittest.mock import patch
from dataclasses import replace,FrozenInstanceError
import agent_planning as p
import test_agent_governance as gf
import test_agent_collaboration as cf

def fixture(**kw):
    args=tuple(gf.fixture(**kw));goal=p.make(p.AgentGoal,goal_id='goal',owner_agent_id='owner',objective='approved local tasks',success_criteria=('ALL_TASKS_COMPLETED',),constraints=('LOCAL_ONLY','NO_RETRY'),authorized_capabilities=('READ_CONTEXT',),resource_budget=10)
    host=p.HostApproval(goal.goal_commitment,(p.digest(args),),'0'*64);plan=p.build(goal,args,host)[0];state=p.initial(goal,plan);host=replace(host,expected_state=state.state_commitment,execution_plans=(plan.plan_commitment,));return goal,plan,state,args,host
class Tests(unittest.TestCase):
    def setUp(self):self.g,self.p,self.s,self.a,self.h=fixture()
    def execute(self,**kw):return p.execute(self.g,self.p,self.s,self.a,self.h,**kw)
    def build_args(self,a):return p.build(self.g,a,replace(self.h,source_commitments=(p.digest(a),)))
    def test01_frozen(self):self.assertRaises(FrozenInstanceError,setattr,self.g,'resource_budget',1)
    def test02_version(self):self.assertRaises(ValueError,replace,self.g,schema_version='bad')
    def test03_bool(self):self.assertRaises(ValueError,replace,self.g,resource_budget=True)
    def test04_negative(self):self.assertRaises(ValueError,replace,self.g,resource_budget=-1)
    def test05_commitment(self):self.assertRaises(ValueError,replace,self.p,plan_commitment='0'*64)
    def test06_unknown(self):self.assertRaises(TypeError,p.AgentGoal,unknown=1)
    def test07_decomposition(self):self.assertEqual(p.build(self.g,self.a,self.h)[1].subgoal_ids,('A','E','B','F','C'))
    def test08_feasible(self):self.assertEqual(p.build(self.g,self.a,self.h)[2].feasibility_status,'FEASIBLE')
    def test09_no_mutation(self):before=p.digest(self.a);p.build(self.g,self.a,self.h);self.assertEqual(before,p.digest(self.a))
    def test10_estimates(self):self.assertEqual(self.p.total_estimated_cost,10)
    def test11_bound_goal(self):self.assertEqual(self.p.goal_commitment,self.g.goal_commitment)
    def test12_capabilities(self):self.assertTrue(all(t.required_capabilities==('READ_CONTEXT',) for t in self.p.ordered_tasks))
    def test13_duplicate(self):
        a=list(self.a);a[2]=(a[2][0],)*5;self.assertRaises(ValueError,self.build_args,tuple(a))
    def test14_missing_dep(self):
        a=list(self.a);a[2]=(replace(a[2][0],dependencies=('missing',)),)+a[2][1:];self.assertRaisesRegex(ValueError,'MISSING_DEPENDENCY',self.build_args,tuple(a))
    def test15_cycle(self):
        a=list(self.a);a[2]=(replace(a[2][0],dependencies=('C',)),)+a[2][1:];self.assertRaisesRegex(ValueError,'CYCLE',self.build_args,tuple(a))
    def test16_edges(self):self.assertIn(('A','B'),self.p.dependency_edges)
    def test17_order(self):ids=tuple(t.task_id for t in self.p.ordered_tasks);self.assertLess(ids.index('B'),ids.index('C'))
    def test18_empty(self):
        a=list(self.a);a[2]=();self.assertRaises(ValueError,self.build_args,tuple(a))
    def test19_goal_authority(self):self.assertRaises(ValueError,p.build,self.g,self.a,replace(self.h,goal_commitment='0'*64))
    def test20_task_authority(self):self.assertRaises(ValueError,p.build,self.g,self.a,replace(self.h,source_commitments=()))
    def test21_capability_denied(self):
        g=p.make(p.AgentGoal,goal_id='goal',owner_agent_id='owner',objective='local',success_criteria=('ALL_TASKS_COMPLETED',),constraints=('LOCAL_ONLY','NO_RETRY'),authorized_capabilities=(),resource_budget=10)
        self.assertRaisesRegex(ValueError,'CAPABILITY',p.build,g,self.a,replace(self.h,goal_commitment=g.goal_commitment))
    def test22_execution_denied(self):self.assertRaises(ValueError,p.execute,self.g,self.p,self.s,self.a,replace(self.h,execution_plans=()))
    def test23_production(self):self.assertRaises(ValueError,replace,self.execute()[1],production_authorized=True)
    def test24_knowledge(self):self.assertRaises(ValueError,replace,self.execute()[1],knowledge_promotion_authorized=True)
    def test25_consumption(self):s=self.execute()[0];self.assertEqual((s.consumed_budget,s.remaining_budget),(5,5))
    def test26_insufficient(self):
        a=list(self.a);a[1]=replace(a[1],global_budget=9);a[4]=replace(a[4],policy_commitment=p.gov.digest(a[1]));self.assertRaisesRegex(ValueError,'INSUFFICIENT_BUDGET',self.build_args,tuple(a))
    def test27_overflow(self):self.assertRaises(ValueError,replace,self.g,resource_budget=10**30)
    def test28_uncertain(self):
        with patch.object(p.gov.ar,'execute',side_effect=RuntimeError()):s=self.execute()[0]
        self.assertEqual((s.consumed_budget,s.uncertain_consumption,s.remaining_budget),(0,4,6))
    def test29_uncertain_retry(self):
        with patch.object(p.gov.ar,'execute',side_effect=RuntimeError()):s=self.execute()[0]
        self.assertRaisesRegex(ValueError,'RETRY_DISABLED',p.execute,self.g,self.p,s,self.a,replace(self.h,expected_state=s.state_commitment))
    def revision_host(self,s=None,plan=None):
        s=s or self.s;plan=plan or self.p;pin=p.digest((s.state_commitment,plan.plan_commitment,p.digest(self.a),'UNAVAILABLE_AGENT'));return replace(self.h,expected_state=s.state_commitment,revision_approvals=(pin,))
    def test30_revision(self):new,s,r=p.revise(self.g,self.p,self.s,self.a,self.revision_host(),'UNAVAILABLE_AGENT');self.assertEqual((new.plan_version,s.revision_count),(1,1));self.assertEqual(r.previous_plan_commitment,self.p.plan_commitment)
    def test31_revision_denied(self):self.assertRaises(ValueError,p.revise,self.g,self.p,self.s,self.a,self.h,'UNAVAILABLE_AGENT')
    def test32_stale_revision(self):self.assertRaises(ValueError,p.revise,self.g,self.p,self.s,self.a,replace(self.revision_host(),expected_state='0'*64),'UNAVAILABLE_AGENT')
    def test33_post_execution_closed(self):
        s=self.execute()[0];self.assertRaisesRegex(ValueError,'POST_EXECUTION',p.revise,self.g,self.p,s,self.a,self.revision_host(s),'FAILED_TASK')
    def test34_revision_limit(self):
        plan=self.p;s=self.s
        for _ in range(4):plan,s,r=p.revise(self.g,plan,s,self.a,self.revision_host(s,plan),'UNAVAILABLE_AGENT')
        self.assertRaisesRegex(ValueError,'REVISION_LIMIT',p.revise,self.g,plan,s,self.a,self.revision_host(s,plan),'UNAVAILABLE_AGENT')
    def test35_replay(self):self.assertTrue(p.replay_equal(self.execute(),self.execute()))
    def test36_stop(self):self.assertRaisesRegex(ValueError,'STOPPED',self.execute,stop=True)
    def test37_deadline(self):self.assertRaisesRegex(ValueError,'DEADLINE',self.execute,now=1,deadline=1)
    def test38_failed_dependency(self):
        g,plan,s,a,h=fixture(bad=True);out=p.execute(g,plan,s,a,h);self.assertEqual(out[0].blocked_task_ids,('B','C'));self.assertEqual(out[1].execution_status,'PARTIAL')
    def test39_governance_stop(self):
        a=list(self.a);a[7]=tuple((True,i) for i in range(5));a=tuple(a);h=replace(self.h,source_commitments=(p.digest(a),));plan=p.build(self.g,a,h)[0];s=p.initial(self.g,plan);h=replace(h,expected_state=s.state_commitment,execution_plans=(plan.plan_commitment,));self.assertEqual(p.execute(self.g,plan,s,a,h)[1].execution_status,'STOPPED')
    def test40_revision_stop(self):self.assertRaisesRegex(ValueError,'STOPPED',p.revise,self.g,self.p,self.s,self.a,self.revision_host(),'UNAVAILABLE_AGENT',stop=True)
    def test41_real_governance(self):self.assertEqual(len(self.execute()[2][3]),5)
    def test42_actual_observations(self):self.assertEqual(self.execute()[2][3][0][1][1].observations[0].execution_status,'SUCCESS')
    def test43_memory_ingestion(self):self.assertEqual(len(p.memory.ingest_governance(self.a,self.execute()[2])),5)
    def test44_stateful_collaboration(self):
        a=tuple(cf.setup());previous=p.collaboration.initial(a[0]);h=replace(self.h,context_approvals=(p.digest((a,previous)),));r=p.diagnostic_context(self.g,self.p,self.s,h,a,previous);self.assertEqual(r[0].consumed_budget,1)
        b=tuple(cf.continued(list(a),r[0]));h=replace(h,context_approvals=(p.digest((b,r[0])),));second=p.diagnostic_context(self.g,self.p,self.s,h,b,r[0]);self.assertEqual(second[0].consumed_budget,2)
    def test45_context_denied(self):
        a=tuple(cf.setup());self.assertRaises(ValueError,p.diagnostic_context,self.g,self.p,self.s,self.h,a,p.collaboration.initial(a[0]))
    def test46_changed_replay(self):self.assertFalse(p.replay_equal(self.execute(),self.execute()[:2]))
    def test47_no_independent_verification(self):self.assertEqual(self.execute()[1].verification_status,'NOT_ESTABLISHED')
if __name__=='__main__':unittest.main()
