"""One bounded hash cycle. Original snapshots remain separate from charged state."""
from hashlib import sha256
from dataclasses import fields
from cognitive_contracts import ContractError,require,ResourcesV1,TaskStepV1,TaskResultV1,TaskTransitionV1
from cognitive_runtime import apply_transition
from cognitive_planner import construct_plan,ready_steps,apply_decision
from cognitive_plan_contracts import PlanDecisionV1
from cognitive_tool_contracts import request_commitment,progress_commitment
from cognitive_tool_adapter import execute_isolated
from cognitive_verification_contracts import VerificationRequestV1
from cognitive_evidence_verifier import verify_original_evidence
from cognitive_knowledge_adapter import propose_knowledge
from cognitive_orchestrator_contracts import OrchestrationRequestV1,OrchestrationOutcomeV1,OrchestrationTraceV1

def _transition(state,kind,when,usage=None,step=None,result=None):
    return apply_transition(state,TaskTransitionV1('cog-transition-v1',state.task.task_id,
        state.task.revision,kind,when,usage,step,result,(),None))

def run_cycle(value: OrchestrationRequestV1) -> OrchestrationOutcomeV1:
    state=progress=evidence=verification=proposal=trace=None
    stage='INPUT'; attempted=False; preflight=False
    def outcome(status,reason):
        nonlocal trace
        if preflight:
            trace=OrchestrationTraceV1('cog-orchestration-trace-v1',value.state.task.task_id,
                value.state.task.revision,state.task.revision,value.plan.plan_id,
                value.progress.revision,progress.revision,value.tool_request.step_id,
                request_commitment(value.tool_request),
                evidence.result.commitment if evidence else None,
                evidence.commitment if evidence else None,
                verification.verification_id if verification else None,
                proposal.proposal_id if proposal else None,
                value.state.task.budget,state.task.budget,attempted,status,value.timestamp)
        return OrchestrationOutcomeV1('cog-orchestration-outcome-v1',status,reason,
            state,progress,evidence,verification,proposal,trace,
            'TRUSTED_COMPLETION_UNAVAILABLE',False,False,False)
    try:
        require(type(value) is OrchestrationRequestV1,'INPUT_TYPE')
        value.__post_init__()
        stage='TASK'; value.state.__post_init__(); state=value.state
        require(value.expected_task_revision==state.task.revision,'STALE_TASK')
        require(state.task.status=='VALIDATED','TASK_STATUS')
        stage='PLAN'
        value.plan.__post_init__(); value.progress.__post_init__(); progress=value.progress
        require(construct_plan(state,value.plan.steps)==value.plan,'PLAN_BINDING')
        ready=ready_steps(value.plan,progress)
        stage='REQUEST'; r=value.tool_request; r.__post_init__()
        require((r.task_id,r.plan_id,r.progress_revision)==(state.task.task_id,value.plan.plan_id,progress.revision),'REQUEST_BINDING')
        require(ready==(r.step_id,),'ONE_READY_STEP_REQUIRED')
        step=next(s for s in progress.steps if s.step_id==r.step_id)
        require(step.status=='PENDING','RETRIES_UNSUPPORTED')
        stage='BINDING'
        if value.binding is None:
            return outcome('CYCLE_DEPENDENCY_UNAVAILABLE','EXPLICIT_BINDING_REQUIRED')
        b=value.binding; b.__post_init__()
        require((b.plan_id,b.step_id,b.symbolic_operation,b.tool_operation,b.request_digest,b.progress_digest)==
                (value.plan.plan_id,r.step_id,step.operation,r.operation,request_commitment(r),progress_commitment(progress)),'BINDING')
        stage='USAGE'; value.usage.__post_init__()
        # Exactly one real adapter invocation, no model invocation. Token/time are declared inputs.
        require(value.usage.steps==1 and value.usage.tool_calls==1 and value.usage.model_calls==0,'USAGE_COUNTS')
        stage='BUDGET'
        for f in fields(ResourcesV1):
            require(getattr(state.task.budget.consumed,f.name)+getattr(value.usage,f.name)<=getattr(state.task.budget.maximum,f.name),'BUDGET_EXHAUSTED')
        preflight=True
        # Prepare all local accounting transitions before publishing any new state.
        stage='LIFECYCLE'
        charged=state
        for kind in ('PLAN','READY','START'): charged=_transition(charged,kind,value.timestamp)
        charged=_transition(charged,'CONSUME',value.timestamp,value.usage,
                            TaskStepV1('cog-step-v1',r.step_id,'Isolated SHA256_TEXT_V1 computation'))
        require(charged.task.status=='RUNNING','CHARGE_FAILED')
        planned_progress=apply_decision(value.plan,progress,PlanDecisionV1(
            'cog-plan-decision-v1',value.plan.plan_id,progress.revision,r.step_id,'COMPLETE'))
        state=charged
        stage='TOOL'; attempted=True
        candidate=execute_isolated(value.state,value.plan,value.progress,r,b)
        original=VerificationRequestV1('cog-verification-request-v1',value.state,
            value.plan,value.progress,r,b,candidate)
        stage='VERIFICATION'
        checked=verify_original_evidence(original)
        require(checked.status=='EVIDENCE_VERIFIED_ISOLATED','VERIFICATION_REJECTED')
        evidence=candidate; verification=checked
        stage='KNOWLEDGE'
        knowledge=propose_knowledge(original)  # Mandatory internal COG-004 recheck is preserved.
        require(knowledge.status=='KNOWLEDGE_PROPOSED_ISOLATED' and
                knowledge.proposal.knowledge_category=='COMPUTED_FACT_ISOLATED','KNOWLEDGE_REJECTED')
        proposal=knowledge.proposal
        stage='SUBMIT'
        content=evidence.result.sha256_hex
        state=_transition(state,'SUBMIT',value.timestamp,result=TaskResultV1(
            'cog-result-v1',content,sha256(content.encode('utf-8')).hexdigest(),'UNVERIFIED'))
        progress=planned_progress
        return outcome('ISOLATED_CYCLE_SUCCEEDED','COMPUTATION_AND_PROPOSAL_ONLY')
    except (ContractError,ValueError,TypeError,AttributeError,StopIteration,RecursionError) as exc:
        budget=(stage=='BUDGET' or (stage=='PLAN' and getattr(exc,'code',None)=='BUDGET_INFEASIBLE'))
        return outcome('CYCLE_BUDGET_EXHAUSTED' if budget else 'CYCLE_REJECTED',
                       'BUDGET_INSUFFICIENT' if budget else stage+'_REJECTED')
