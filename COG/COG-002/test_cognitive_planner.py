import unittest
from dataclasses import replace, FrozenInstanceError
from cognitive_contracts import *
from cognitive_runtime import apply_transition
from cognitive_plan_contracts import *
from cognitive_planner import *

A='00000000-0000-0000-0000-000000000001'
B='00000000-0000-0000-0000-000000000002'
T='2026-10-15T00:00:00.000000Z'
def fixture():
    task=CognitiveTaskV1(A,'cog-task-v1','explicit objective',T,1,'CREATED',0,TaskBudgetV1('cog-budget-v1',ResourcesV1(10,10,10,100,1000),ResourcesV1(0,0,0,0,0)),(),(),None,None)
    state=CognitiveStateV1('cog-state-v1',task,())
    state=apply_transition(state,TaskTransitionV1('cog-transition-v1',A,0,'VALIDATE',T,None,None,None,(),None))
    a=PlanStepV1('cog-plan-step-v1',A,'ANALYZE',(),ResourcesV1(1,0,0,2,3),1,'PENDING',0)
    b=PlanStepV1('cog-plan-step-v1',B,'SYNTHESIZE',(A,),ResourcesV1(1,0,0,2,3),0,'PENDING',0)
    return state,(a,b)
def setup():
    s,steps=fixture(); p=construct_plan(s,steps)
    return p,initial_progress(p)
def decide(p,x,step,action):
    return apply_decision(p,x,PlanDecisionV1('cog-plan-decision-v1',p.plan_id,x.revision,step,action))

class PlannerTests(unittest.TestCase):
    def test_plan(self):
        p,x=setup(); self.assertEqual(len(p.steps),2); self.assertEqual(x.outcome,'ACTIVE')
    def test_identity(self):
        s,steps=fixture(); self.assertEqual(construct_plan(s,steps).plan_id,construct_plan(s,steps[::-1]).plan_id)
    def test_order(self):
        p,x=setup()
        with self.assertRaises(ContractError): decide(p,x,B,'COMPLETE')
    def test_cycle(self):
        s,(a,b)=fixture()
        with self.assertRaisesRegex(ContractError,'CYCLE'): construct_plan(s,(replace(a,dependencies=(B,)),b))
    def test_duplicate(self):
        s,(a,b)=fixture()
        with self.assertRaisesRegex(ContractError,'DUPLICATE_STEP'): construct_plan(s,(a,a))
    def test_missing(self):
        s,(a,b)=fixture()
        with self.assertRaisesRegex(ContractError,'MISSING_DEPENDENCY'): construct_plan(s,(b,))
    def test_ready(self):
        p,x=setup(); self.assertEqual(ready_steps(p,x),(A,))
        x=decide(p,x,A,'COMPLETE'); self.assertEqual(ready_steps(p,x),(B,))
    def test_success(self):
        p,x=setup(); x=decide(p,x,A,'COMPLETE'); x=decide(p,x,B,'COMPLETE')
        self.assertEqual(x.outcome,'COMPLETED'); self.assertEqual(x.revision,2); self.assertEqual(ready_steps(p,x),())
    def test_fail(self):
        p,x=setup(); x=decide(p,x,A,'FAIL'); self.assertEqual(x.steps[0].status,'FAILED')
    def test_retry(self):
        p,x=setup(); x=decide(p,x,A,'FAIL'); x=decide(p,x,A,'RETRY_COMPLETE')
        self.assertEqual(x.steps[0].attempts,2); self.assertEqual(x.consumed_estimate.steps,2)
    def test_exhaustion(self):
        p,x=setup(); x=decide(p,x,A,'FAIL'); x=decide(p,x,A,'RETRY_FAIL')
        self.assertEqual(x.outcome,'FAILED')
        with self.assertRaises(ContractError): decide(p,x,A,'RETRY_COMPLETE')
    def test_stale(self):
        p,x=setup(); d=PlanDecisionV1('cog-plan-decision-v1',p.plan_id,0,A,'COMPLETE'); x=apply_decision(p,x,d)
        with self.assertRaisesRegex(ContractError,'STALE_REVISION'): apply_decision(p,x,d)
    def test_budget(self):
        s,(a,b)=fixture()
        for name in ('steps','tool_calls','model_calls','tokens','time_ms'):
            with self.subTest(name=name), self.assertRaises(ContractError):
                if name=='steps':
                    a2=replace(a,max_retries=3); b2=replace(b,max_retries=3)
                    s2=replace(s.task.budget,maximum=replace(s.task.budget.maximum,steps=7))
                    # Rebuild valid task/state through initial genesis, not alter an event head.
                    task=replace(s.task,status='CREATED',revision=0,budget=s2)
                    st=CognitiveStateV1('cog-state-v1',task,())
                    st=apply_transition(st,TaskTransitionV1('cog-transition-v1',A,0,'VALIDATE',T,None,None,None,(),None))
                    construct_plan(st,(a2,b2))
                else:
                    construct_plan(s,(replace(a,estimate=replace(a.estimate,**{name:1001})),b))
    def test_unknown(self):
        s,(a,b)=fixture()
        with self.assertRaises(ContractError): replace(a,operation='EXECUTE_TOOL')
    def test_immutable(self):
        s,steps=fixture(); raw=canonical_bytes(s); p=construct_plan(s,steps); x=initial_progress(p); old=canonical_bytes(x)
        decide(p,x,A,'FAIL'); self.assertEqual(raw,canonical_bytes(s)); self.assertEqual(old,canonical_bytes(x))
        with self.assertRaises(FrozenInstanceError): x.revision=8
    def test_no_authority(self):
        p,x=setup(); self.assertFalse(p.executable); self.assertFalse(x.executable)
        self.assertFalse(PlanDecisionV1('cog-plan-decision-v1',p.plan_id,0,A,'COMPLETE').executable)
    def test_no_implicit_retry(self):
        p,x=setup(); x=decide(p,x,A,'FAIL')
        with self.assertRaisesRegex(ContractError,'EXPLICIT_RETRY_REQUIRED'): decide(p,x,A,'COMPLETE')
    def test_completed_rewrite(self):
        p,x=setup(); x=decide(p,x,A,'COMPLETE')
        with self.assertRaises(ContractError): decide(p,x,A,'FAIL')
    def test_changed_definition(self):
        p,x=setup()
        with self.assertRaises(ContractError): ready_steps(p,replace(x,steps=(replace(x.steps[0],operation='SYNTHESIZE'),x.steps[1])))
    def test_bad_estimate(self):
        with self.assertRaises(ContractError): ResourcesV1(1,0,0,-1,0)
    def test_overflow(self):
        s,(a,b)=fixture()
        with self.assertRaisesRegex(ContractError,'ESTIMATE_OVERFLOW'): construct_plan(s,(replace(a,estimate=ResourcesV1(1,MAX,0,0,0)),b))
    def test_retry_bound(self):
        s,(a,b)=fixture()
        with self.assertRaises(ContractError): replace(a,max_retries=4)
    def test_wrong_plan(self):
        p,x=setup()
        with self.assertRaises(ContractError): apply_decision(p,x,PlanDecisionV1('cog-plan-decision-v1','0'*64,0,A,'COMPLETE'))
    def test_requires_validated(self):
        s,_=fixture(); s=apply_transition(s,TaskTransitionV1('cog-transition-v1',A,1,'PLAN',T,None,None,None,(),None))
        with self.assertRaisesRegex(ContractError,'VALIDATED_TASK_REQUIRED'): construct_plan(s,fixture()[1])
