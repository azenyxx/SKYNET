"""Pure isolated lifecycle. Resource counts describe supplied simulated work only."""
from dataclasses import fields, replace
from cognitive_contracts import (CognitiveStateV1,TaskTransitionV1,ResourcesV1,TERMINAL,MAX,require)
from cognitive_events import make_event

EDGES = (('VALIDATE','CREATED','VALIDATED'),('PLAN','VALIDATED','PLANNED'),('READY','PLANNED','READY'),('START','READY','RUNNING'),('SUBMIT','RUNNING','VERIFYING'),('COMPLETE','VERIFYING','COMPLETED'))

def apply_transition(current_state: CognitiveStateV1, transition: TaskTransitionV1) -> CognitiveStateV1:
    require(type(current_state) is CognitiveStateV1 and type(transition) is TaskTransitionV1,'INPUT_TYPE')
    current_state.__post_init__()
    transition.__post_init__()
    task=current_state.task
    require(transition.task_id==task.task_id,'TARGET')
    require(transition.expected_revision==task.revision,'STALE_REVISION')
    require(task.revision<MAX and len(current_state.events)<10000,'REVISION_LIMIT')
    require(task.status not in TERMINAL,'TERMINAL')
    require(transition.timestamp >= (current_state.events[-1].timestamp if current_state.events else task.created_at),'TIME_REGRESSION')
    kind=transition.transition_type
    updates={}
    if kind in ('FAIL','CANCEL','BLOCK'):
        require(task.status!='BLOCKED' or kind in ('FAIL','CANCEL'),'INVALID_TRANSITION')
        updates=dict(status={'FAIL':'FAILED','CANCEL':'CANCELLED','BLOCK':'BLOCKED'}[kind],failure_reason=transition.reason,result=None)
    elif kind=='CONSUME':
        require(task.status=='RUNNING','INVALID_TRANSITION')
        delta=transition.consumption
        require(delta is not None and any(getattr(delta,f.name)>0 for f in fields(ResourcesV1)),'EMPTY_CONSUMPTION')
        require(delta.steps in (0,1) and (transition.step is not None)==(delta.steps==1),'STEP_CONSUMPTION')
        require(transition.step is None or transition.step.step_id not in {s.step_id for s in task.steps},'DUPLICATE_STEP')
        totals={f.name:getattr(task.budget.consumed,f.name)+getattr(delta,f.name) for f in fields(ResourcesV1)}
        require(all(v<=MAX for v in totals.values()),'INTEGER_OVERFLOW')
        exhausted=tuple(k for k,v in totals.items() if v>getattr(task.budget.maximum,k))
        if exhausted:
            updates=dict(status='BLOCKED',failure_reason='BUDGET_EXHAUSTED:'+','.join(exhausted))
        else:
            updates=dict(budget=replace(task.budget,consumed=ResourcesV1(**totals)),steps=task.steps+((transition.step,) if transition.step else ()))
    elif kind=='VERIFY_SIMULATED':
        require(task.status=='VERIFYING' and task.result is not None and task.result.verification=='UNVERIFIED','INVALID_TRANSITION')
        # Test-only exact-echo verifier. References do not establish authenticity.
        require(task.result.content==task.objective and any(e.content_hash==task.result.content_hash for e in task.evidence_refs),'SIMULATED_VERIFICATION_FAILED')
        updates=dict(result=replace(task.result,verification='VERIFICATION_SIMULATED'))
    else:
        edge=next((x for x in EDGES if x[0]==kind and x[1]==task.status),None)
        require(edge is not None,'INVALID_TRANSITION')
        updates=dict(status=edge[2])
        if kind=='SUBMIT':
            require(transition.result.verification=='UNVERIFIED','TRUST_BOUNDARY')
            updates.update(result=transition.result,evidence_refs=transition.evidence_refs)
        if kind=='COMPLETE':
            require(task.result is not None and task.result.verification=='VERIFICATION_SIMULATED','VERIFICATION_REQUIRED')
    after=replace(task,revision=task.revision+1,**updates)
    event=make_event(task,after,transition,current_state.events[-1].event_digest if current_state.events else '0'*64)
    return CognitiveStateV1('cog-state-v1',after,current_state.events+(event,))
