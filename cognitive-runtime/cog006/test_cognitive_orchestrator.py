import unittest
from dataclasses import replace,asdict
from unittest.mock import patch
from pathlib import Path
import ast
from cognitive_contracts import *
from cognitive_runtime import apply_transition
from cognitive_planner import construct_plan,initial_progress
from cognitive_plan_contracts import PlanStepV1
from cognitive_tool_contracts import *
from cognitive_orchestrator_contracts import *
from cognitive_orchestrator import run_cycle
from test_cognitive_evidence_verifier import corrupt

A='00000000-0000-0000-0000-000000000001'
B='00000000-0000-0000-0000-000000000002'
R='00000000-0000-0000-0000-000000000003'
T='2026-10-15T00:00:00.000000Z'
def fixture(maximum=None,usage=None):
    maximum=maximum or ResourcesV1(10,10,0,100,1000)
    task=CognitiveTaskV1(A,'cog-task-v1','hash demonstration',T,1,'CREATED',0,TaskBudgetV1('cog-budget-v1',maximum,ResourcesV1(0,0,0,0,0)),(),(),None,None)
    state=CognitiveStateV1('cog-state-v1',task,())
    state=apply_transition(state,TaskTransitionV1('cog-transition-v1',A,0,'VALIDATE',T,None,None,None,(),None))
    step=PlanStepV1('cog-plan-step-v1',B,'ANALYZE',(),ResourcesV1(1,0,0,0,0),0,'PENDING',0)
    plan=construct_plan(state,(step,)); progress=initial_progress(plan)
    r=ToolRequestV1('cog-tool-request-v1',A,plan.plan_id,B,0,'SHA256_TEXT_V1',input_digest('abc'),R,'abc')
    b=IsolatedToolBindingV1('cog-isolated-tool-binding-v1','ISOLATED_LOCAL_ONLY',plan.plan_id,B,'ANALYZE','SHA256_TEXT_V1',request_commitment(r),progress_commitment(progress))
    return OrchestrationRequestV1('cog-orchestration-request-v1',state,1,plan,progress,r,b,usage or ResourcesV1(1,1,0,2,3),T)

class CycleTests(unittest.TestCase):
    def test_positive(self):
        o=run_cycle(fixture()); self.assertEqual(o.status,'ISOLATED_CYCLE_SUCCEEDED')
        self.assertEqual(o.state.task.status,'VERIFYING'); self.assertEqual(o.progress.outcome,'COMPLETED')
    def test_real_tool(self):
        o=run_cycle(fixture()); self.assertEqual(o.evidence.result.sha256_hex,'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    def test_real_verifier(self):
        o=run_cycle(fixture()); self.assertEqual(o.verification.status,'EVIDENCE_VERIFIED_ISOLATED')
    def test_real_proposal(self):
        o=run_cycle(fixture()); self.assertEqual(o.proposal.knowledge_category,'COMPUTED_FACT_ISOLATED')
    def bad_request(self,**kw):
        v=fixture(); o=run_cycle(replace(v,tool_request=corrupt(v.tool_request,**kw)))
        self.assertEqual(o.status,'CYCLE_REJECTED'); self.assertEqual(o.state,v.state)
    def test_task(self): self.bad_request(task_id=B)
    def test_plan(self): self.bad_request(plan_id='0'*64)
    def test_step(self): self.bad_request(step_id=R)
    def test_stale(self): self.bad_request(progress_revision=1)
    def test_stale_task(self):
        v=fixture(); self.assertEqual(run_cycle(replace(v,expected_task_revision=0)).reason,'TASK_REJECTED')
    def test_nonready(self):
        v=fixture()
        from cognitive_planner import apply_decision
        from cognitive_plan_contracts import PlanDecisionV1
        done=apply_decision(v.plan,v.progress,PlanDecisionV1('cog-plan-decision-v1',v.plan.plan_id,0,B,'COMPLETE'))
        self.assertEqual(run_cycle(replace(v,progress=done,tool_request=replace(v.tool_request,progress_revision=1))).status,'CYCLE_REJECTED')
    def test_missing_binding(self): self.assertEqual(run_cycle(replace(fixture(),binding=None)).status,'CYCLE_DEPENDENCY_UNAVAILABLE')
    def test_unknown(self): self.bad_request(operation='SHELL')
    def test_steps(self):
        v=fixture()
        # A coherent constrained task has no feasible one-step plan: reject before execution.
        from cognitive_contracts import task_digest
        task=replace(v.state.task,status='CREATED',revision=0,budget=TaskBudgetV1('cog-budget-v1',ResourcesV1(0,10,0,100,1000),ResourcesV1(0,0,0,0,0)))
        s=CognitiveStateV1('cog-state-v1',task,())
        s=apply_transition(s,TaskTransitionV1('cog-transition-v1',A,0,'VALIDATE',T,None,None,None,(),None))
        p=replace(v.plan,task_commitment=task_digest(s.task))
        self.assertEqual(run_cycle(replace(v,state=s,plan=p)).status,'CYCLE_BUDGET_EXHAUSTED')
    def test_tools(self): self.assertEqual(run_cycle(fixture(maximum=ResourcesV1(10,0,0,100,1000))).status,'CYCLE_BUDGET_EXHAUSTED')
    def test_models(self):
        self.assertEqual(run_cycle(fixture(usage=ResourcesV1(1,1,1,0,0))).reason,'USAGE_REJECTED')
        self.assertEqual(run_cycle(fixture()).status,'ISOLATED_CYCLE_SUCCEEDED') # zero model budget, zero calls
    def test_tokens(self): self.assertEqual(run_cycle(fixture(usage=ResourcesV1(1,1,0,101,0))).status,'CYCLE_BUDGET_EXHAUSTED')
    def test_time(self): self.assertEqual(run_cycle(fixture(usage=ResourcesV1(1,1,0,0,1001))).status,'CYCLE_BUDGET_EXHAUSTED')
    def test_accounting(self):
        o=run_cycle(fixture()); self.assertEqual(o.state.task.budget.consumed,ResourcesV1(1,1,0,2,3))
        self.assertEqual(o.state.task.revision,6)
    def test_preflight_no_partial(self):
        v=fixture(maximum=ResourcesV1(10,0,0,100,1000))
        with patch('cognitive_orchestrator.execute_isolated',side_effect=AssertionError):
            o=run_cycle(v)
        self.assertEqual(o.state,v.state); self.assertEqual(o.progress,v.progress)
    def test_determinism(self):
        v=fixture(); self.assertEqual(run_cycle(v).trace.trace_id,run_cycle(v).trace.trace_id)
    def test_tamper(self):
        from cognitive_tool_adapter import execute_isolated
        def damaged(*args):
            e=execute_isolated(*args)
            return corrupt(e,commitment='0'*64)
        v=fixture()
        with patch('cognitive_orchestrator.execute_isolated',side_effect=damaged):
            o=run_cycle(v)
        self.assertEqual(o.status,'CYCLE_REJECTED'); self.assertEqual(o.reason,'VERIFICATION_REJECTED')
        self.assertEqual(o.state.task.budget.consumed.tool_calls,1); self.assertEqual(o.progress,v.progress)
        self.assertIsNone(o.proposal)
    def test_no_mutation(self):
        v=fixture(); before=asdict(v); run_cycle(v); self.assertEqual(before,asdict(v))
    def test_no_memory_writes(self):
        v=fixture()
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError):
            self.assertEqual(run_cycle(v).status,'ISOLATED_CYCLE_SUCCEEDED')
    def test_no_world_import(self):
        tree=ast.parse(Path(__file__).with_name('cognitive_orchestrator.py').read_text())
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and ('world' in n.module or 'services' in n.module) for n in ast.walk(tree)))
    def test_no_authority(self):
        o=run_cycle(fixture()); self.assertFalse(o.production_authorized); self.assertFalse(o.persisted)
    def test_no_completion(self):
        o=run_cycle(fixture()); self.assertEqual(o.state.task.result.verification,'UNVERIFIED')
        self.assertFalse(o.trusted_verification); self.assertEqual(o.completion_reason,'TRUSTED_COMPLETION_UNAVAILABLE')
    def test_stable_failure(self):
        v=replace(fixture(),expected_task_revision=0); self.assertEqual(run_cycle(v),run_cycle(v))
    def test_bad_usage(self):
        v=fixture(); self.assertEqual(run_cycle(replace(v,usage=corrupt(v.usage,tokens=-1))).reason,'USAGE_REJECTED')
    def test_clock_regression(self):
        v=fixture(); o=run_cycle(replace(v,timestamp='2026-10-14T00:00:00.000000Z'))
        self.assertEqual(o.status,'CYCLE_REJECTED'); self.assertEqual(o.state,v.state)
