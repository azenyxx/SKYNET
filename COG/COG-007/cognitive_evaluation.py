"""Sequential deterministic evaluation; no execution mocking or global patches."""
from dataclasses import replace,asdict
from cognitive_contracts import *
from cognitive_runtime import apply_transition
from cognitive_planner import apply_decision
from cognitive_plan_contracts import PlanDecisionV1
from cognitive_orchestrator import run_cycle
from cognitive_verification_contracts import VerificationRequestV1
from cognitive_evidence_verifier import verify_original_evidence
from cognitive_tool_contracts import body_commitment
from cognitive_evaluation_contracts import *
from test_cognitive_orchestrator import fixture as original_fixture
import copy

def _corrupt(value,**changes):
    # Local negative fixture only: never modify a predecessor object in place.
    clone=copy.copy(value)
    for name,v in changes.items(): object.__setattr__(clone,name,v)
    return clone

def build_fixture(case: EvaluationCaseV1):
    require(type(case) is EvaluationCaseV1,'CASE_TYPE'); case.__post_init__()
    v=original_fixture(); kind=case.scenario
    if kind in ('TASK_REVISION','STABLE_FAILURE'): return replace(v,expected_task_revision=0)
    if kind=='PLAN_REVISION': return replace(v,plan=replace(v.plan,task_revision=v.plan.task_revision+1))
    if kind=='MISSING_BINDING': return replace(v,binding=None)
    if kind=='NONREADY':
        p=apply_decision(v.plan,v.progress,PlanDecisionV1('cog-plan-decision-v1',v.plan.plan_id,0,v.tool_request.step_id,'COMPLETE'))
        return replace(v,progress=p,tool_request=replace(v.tool_request,progress_revision=1))
    if kind=='UNSUPPORTED': return replace(v,tool_request=_corrupt(v.tool_request,operation='NOT_ALLOWLISTED'))
    if kind=='TOOL_BUDGET': return original_fixture(maximum=ResourcesV1(10,0,0,100,1000))
    if kind=='STEP_BUDGET':
        task=replace(v.state.task,status='CREATED',revision=0,budget=TaskBudgetV1('cog-budget-v1',ResourcesV1(0,10,0,100,1000),ResourcesV1(0,0,0,0,0)))
        s=CognitiveStateV1('cog-state-v1',task,())
        s=apply_transition(s,TaskTransitionV1('cog-transition-v1',task.task_id,0,'VALIDATE',v.timestamp,None,None,None,(),None))
        return replace(v,state=s,plan=replace(v.plan,task_commitment=task_digest(s.task)))
    if kind=='INVALID_TOKENS': return replace(v,usage=_corrupt(v.usage,tokens=-1))
    if kind=='INVALID_TIME': return replace(v,usage=_corrupt(v.usage,time_ms=-1))
    return v

def _observe(case):
    value=build_fixture(case); before=asdict(value)
    out=run_cycle(value)
    observed,reason=out.status,out.reason
    if case.scenario in ('TAMPER_EVIDENCE','REJECT_VERIFICATION'):
        require(out.status=='ISOLATED_CYCLE_SUCCEEDED','POSITIVE_PREREQUISITE')
        e=out.evidence
        if case.scenario=='TAMPER_EVIDENCE':
            e=_corrupt(e,commitment='0'*64)
        else:
            r=_corrupt(e.result,sha256_hex='0'*64)
            r=replace(r,commitment=body_commitment(b'SKYNET:COGToolResultV1:v1\0',r))
            e=_corrupt(e,result=r)
            e=replace(e,commitment=body_commitment(b'SKYNET:COGToolEvidenceV1:v1\0',e))
        checked=verify_original_evidence(VerificationRequestV1('cog-verification-request-v1',
            value.state,value.plan,value.progress,value.tool_request,value.binding,e))
        observed,reason=checked.status,checked.findings[0].code
    flags=[out.production_authorized,out.trusted_verification,out.persisted]
    if out.evidence: flags += [out.evidence.production_authorized,out.evidence.result.production_authorized,out.evidence.decision.production_authorized]
    if out.verification: flags += [out.verification.production_authorized,out.verification.trusted_verification,out.verification.task_completion_authorized]
    if out.proposal: flags += [out.proposal.production_authorized,out.proposal.trusted_knowledge,out.proposal.persisted]
    violations=sum(x is not False for x in flags)
    if out.state and (out.state.task.status=='COMPLETED' or (out.state.task.result and out.state.task.result.verification=='VERIFICATION_TRUSTED')): violations+=1
    semantics=True
    if out.status=='ISOLATED_CYCLE_SUCCEEDED':
        semantics=(out.evidence.result.sha256_hex=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
            and out.evidence.result.input_byte_length==3
            and out.state.task.status=='VERIFYING'
            and out.state.task.result.verification=='UNVERIFIED'
            and out.state.task.revision==6 and out.progress.revision==1
            and out.verification.status=='EVIDENCE_VERIFIED_ISOLATED'
            and out.proposal.knowledge_category=='COMPUTED_FACT_ISOLATED')
    return out,observed,reason,violations,semantics,before==asdict(value)

def evaluate_case(case: EvaluationCaseV1) -> EvaluationResultV1:
    require(type(case) is EvaluationCaseV1,'CASE_TYPE'); case.__post_init__()
    try:
        a,observed,reason,violations,semantics,unchanged=_observe(case)
        b,obs2,reason2,v2,s2,u2=_observe(case)
        trace=a.trace.trace_id if a.trace else None
        trace2=b.trace.trace_id if b.trace else None
        present=case.expected_trace=='PRESENT_IDENTICAL'
        agreement=(trace==trace2 and ((trace is not None)==present))
        logical=(canonical_bytes(a)==canonical_bytes(b) and (observed,reason)==(obs2,reason2))
        outcome_correct=(observed,reason)==(case.expected_outcome,case.expected_reason)
        budget=a.state.task.budget.consumed if a.state else None
        budget_ok=budget==case.expected_budget and b.state is not None and b.state.task.budget.consumed==case.expected_budget
        violations=max(violations,v2) # count violating flags per case, not duplicate replays
        passed=outcome_correct and budget_ok and violations==0 and agreement and logical and unchanged and u2 and semantics and s2
        return EvaluationResultV1('cog-evaluation-result-v1',case.case_id,case.scenario,observed,reason,budget,trace,outcome_correct,budget_ok,violations,present,agreement,logical,unchanged and u2,semantics and s2,False,passed)
    except Exception:
        # Report a failed observation, never turn an exception into an expected rejection.
        return EvaluationResultV1('cog-evaluation-result-v1',case.case_id,case.scenario,'UNEXPECTED_EXCEPTION','EXCEPTION',None,None,False,False,0,case.expected_trace=='PRESENT_IDENTICAL',False,False,False,False,True,False)

def evaluate_suite(cases: tuple[EvaluationCaseV1,...]) -> EvaluationSummaryV1:
    require(type(cases) is tuple and 1<=len(cases)<=64,'CASES')
    for c in cases:
        require(type(c) is EvaluationCaseV1,'CASE_TYPE'); c.__post_init__()
    require(len({c.case_id for c in cases})==len(cases),'DUPLICATE_CASE')
    results=tuple(evaluate_case(c) for c in cases)
    positive=tuple(r for c,r in zip(cases,results) if c.expected_outcome=='ISOLATED_CYCLE_SUCCEEDED')
    negative=tuple(r for c,r in zip(cases,results) if c.expected_outcome!='ISOLATED_CYCLE_SUCCEEDED')
    traces=tuple(r for r in results if r.trace_expected)
    return EvaluationSummaryV1('cog-evaluation-summary-v1',results,len(results),sum(r.passed for r in results),sum(not r.passed for r in results),
        RateV1(sum(r.outcome_correct and r.positive_semantics for r in positive),len(positive)),
        RateV1(sum(r.outcome_correct for r in negative),len(negative)),
        RateV1(sum(r.budget_correct for r in results),len(results)),
        RateV1(sum(r.trace_agrees for r in traces),len(traces)),
        RateV1(sum(r.logical_agreement for r in results),len(results)),
        sum(r.trust_violations for r in results),sum(r.unexpected_exception for r in results))
