"""Bounded deterministic planning and simulated outcome recording. No executors."""
from dataclasses import fields, replace
from cognitive_contracts import CognitiveStateV1, ResourcesV1, MAX, require, task_digest
from cognitive_plan_contracts import PlanV1, PlanStepV1, PlanProgressV1, PlanDecisionV1

def construct_plan(state: CognitiveStateV1, steps: tuple[PlanStepV1,...]) -> PlanV1:
    require(type(state) is CognitiveStateV1,'STATE_TYPE')
    state.__post_init__()
    require(state.task.status=='VALIDATED','VALIDATED_TASK_REQUIRED')
    require(type(steps) is tuple and 1<=len(steps)<=64 and all(type(s) is PlanStepV1 for s in steps),'STEPS')
    plan=PlanV1('cog-plan-v1',state.task.task_id,state.task.revision,task_digest(state.task),tuple(sorted(steps,key=lambda s:s.step_id)))
    for f in fields(ResourcesV1):
        total=sum(getattr(s.estimate,f.name)*(s.max_retries+1) for s in plan.steps)
        require(total<=MAX,'ESTIMATE_OVERFLOW')
        require(total<=getattr(state.task.budget.maximum,f.name)-getattr(state.task.budget.consumed,f.name),'BUDGET_INFEASIBLE')
    return plan

def initial_progress(plan: PlanV1) -> PlanProgressV1:
    require(type(plan) is PlanV1,'PLAN_TYPE')
    plan.__post_init__()
    return PlanProgressV1('cog-plan-progress-v1',plan.plan_id,0,plan.steps,ResourcesV1(0,0,0,0,0),'ACTIVE')

def _validate(plan,progress):
    require(type(plan) is PlanV1 and type(progress) is PlanProgressV1,'INPUT_TYPE')
    plan.__post_init__()
    progress.__post_init__()
    require(progress.plan_id==plan.plan_id,'PLAN_BINDING')
    require(tuple(replace(s,status='PENDING',attempts=0) for s in progress.steps)==plan.steps,'DEFINITION_CHANGED')

def ready_steps(plan: PlanV1, progress: PlanProgressV1) -> tuple[str,...]:
    _validate(plan,progress)
    if progress.outcome!='ACTIVE': return ()
    completed={s.step_id for s in progress.steps if s.status=='COMPLETED'}
    return tuple(s.step_id for s in progress.steps if s.status!='COMPLETED' and s.attempts<s.max_retries+1 and set(s.dependencies)<=completed)

def apply_decision(plan: PlanV1, progress: PlanProgressV1, decision: PlanDecisionV1) -> PlanProgressV1:
    _validate(plan,progress)
    require(type(decision) is PlanDecisionV1,'DECISION_TYPE')
    decision.__post_init__()
    require(decision.plan_id==plan.plan_id,'PLAN_BINDING')
    require(decision.expected_revision==progress.revision,'STALE_REVISION')
    require(progress.outcome=='ACTIVE','TERMINAL')
    require(decision.step_id in ready_steps(plan,progress),'NOT_READY')
    old=next(s for s in progress.steps if s.step_id==decision.step_id)
    require(decision.action.startswith('RETRY_')==(old.status=='FAILED'),'EXPLICIT_RETRY_REQUIRED')
    status='COMPLETED' if decision.action.endswith('COMPLETE') else 'FAILED'
    updated=replace(old,status=status,attempts=old.attempts+1)
    steps=tuple(updated if s.step_id==old.step_id else s for s in progress.steps)
    consumed=ResourcesV1(**{f.name:getattr(progress.consumed_estimate,f.name)+getattr(old.estimate,f.name) for f in fields(ResourcesV1)})
    outcome='FAILED' if updated.status=='FAILED' and updated.attempts==updated.max_retries+1 else ('COMPLETED' if all(s.status=='COMPLETED' for s in steps) else 'ACTIVE')
    return PlanProgressV1('cog-plan-progress-v1',plan.plan_id,progress.revision+1,steps,consumed,outcome)
