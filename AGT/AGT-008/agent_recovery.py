"""Coordination records only. No dispatch, retries, assignment changes or replan.
CONTINUE_READY/reassignment/replan remain NOT_QUALIFIED, never executed.
Source freshness and state freshness rely on trusted host pins; no durable recovery.
"""
from agent_recovery_contracts import *

def source(source_args):
    need(type(source_args) is tuple and len(source_args)==9,'SOURCE_SHAPE')
    need(len(feedback.planning.mc.encoded(source_args))<=262144,'SOURCE_LIMIT')
    result=feedback.evaluate(*source_args)
    return source_args[0],source_args[1],source_args[4][0],result

def initial(source_args):
    goal,plan,state,result=source(source_args)
    return make(RecoveryState,goal_id=goal.goal_id,active_plan_commitment=plan.plan_commitment,processed_request_ids=(),completed_recovery_ids=(),blocked_recovery_ids=(),consumed_budget=state.consumed_budget,uncertain_consumption=state.uncertain_consumption,remaining_budget=state.remaining_budget,reserved_capacity=state.reserved_consumption,source_pin=digest(source_args))

def coordinate(source_args,request,candidate,policy,authorization,previous,host,*,stop=False,now=0,deadline=1):
    for obj,kind in ((request,RecoveryRequest),(candidate,RecoveryCandidate),(policy,RecoveryPolicy),(authorization,RecoveryAuthorization),(previous,RecoveryState),(host,HostPins)):
        need(type(obj) is kind,'CONTRACT');obj.__post_init__()
    feedback.planning.memory.guard(stop,now,deadline,previous.remaining_budget,1)
    need(previous.state_commitment==host.expected_state,'STALE_STATE');need(policy.policy_commitment==host.policy_commitment,'POLICY_PIN')
    need(digest(source_args)==host.source_commitment==previous.source_pin,'SOURCE_PIN')
    goal,plan,ps,fb=source(source_args)
    need(request.goal_id==previous.goal_id==goal.goal_id and request.plan_commitment==previous.active_plan_commitment==plan.plan_commitment,'GOAL_PLAN')
    need(request.source_state_commitment==ps.state_commitment,'SOURCE_STATE')
    need(candidate.request_id==request.request_id and request.request_id not in previous.processed_request_ids,'DUPLICATE_REQUEST')
    need(candidate.candidate_id not in previous.completed_recovery_ids+previous.blocked_recovery_ids,'DUPLICATE_CANDIDATE');need(previous.sequence<policy.max_attempts,'ATTEMPT_LIMIT')
    need(previous.consumed_budget+previous.uncertain_consumption+previous.reserved_capacity+previous.remaining_budget==goal.resource_budget,'CONSERVATION')
    need(previous.uncertain_consumption==ps.uncertain_consumption and previous.reserved_capacity==ps.reserved_consumption and previous.consumed_budget==ps.consumed_budget+previous.sequence,'LIABILITY')
    need(policy.resource_ceiling<=goal.resource_budget and previous.sequence+1<=policy.resource_ceiling,'CEILING')
    need(set(candidate.proposed_operations)<=set(request.requested_operations)<=set(policy.allowed_operations),'OPERATION_SCOPE')
    need(authorization.authorization_commitment in host.authorization_commitments and authorization.candidate_commitment==candidate.candidate_commitment,'AUTHORIZATION_PIN')
    need(authorization.approved_operations==candidate.proposed_operations and candidate.estimated_cost<=authorization.approved_budget<=policy.resource_ceiling,'AUTHORIZED_BUDGET')
    ids=tuple(t.task_id for t in plan.ordered_tasks);need(set(candidate.affected_task_ids)<=set(ids),'UNKNOWN_TASK')
    # Real feedback revalidates AGT003 prepare, including original DAG/capabilities.
    statuses={o.task_id:o.execution_status for o in source_args[4][2][1].task_outcomes}
    affected=tuple(statuses[k] for k in candidate.affected_task_ids)
    if request.reason_code=='TASK_FAILED':need('FAILED' in affected,'REASON')
    if request.reason_code=='DEPENDENCY_BLOCKED':need('BLOCKED' in affected,'REASON')
    if request.reason_code=='EXECUTION_UNCERTAIN':need('UNCERTAIN' in affected,'REASON')
    if request.reason_code=='RESOURCE_PRESSURE':need(ps.remaining_budget==0 or 'BUDGET_EXHAUSTED' in affected,'REASON')
    if request.reason_code=='STOP_REQUESTED':need(source_args[4][1].execution_status=='STOPPED','REASON')
    if request.reason_code=='DEADLINE_REACHED':need(source_args[4][1].execution_status=='DEADLINE','REASON')
    unsupported=tuple(op for op in candidate.proposed_operations if op in ('CONTINUE_READY','REQUEST_REPLAN','REQUEST_REASSIGNMENT'))
    if request.reason_code=='AGENT_UNAVAILABLE':unsupported=unsupported+('AVAILABILITY_EVIDENCE_UNQUALIFIED',)
    status='NOT_QUALIFIED' if unsupported else 'ELIGIBLE'
    evaluation=make(RecoveryEvaluation,evaluation_id='eval:'+candidate.candidate_commitment,candidate_id=candidate.candidate_id,feasibility_status=status,constraint_violations=unsupported,resource_projection=1)
    core=(previous.state_commitment,digest(host),request.request_commitment,candidate.candidate_commitment,authorization.authorization_commitment,evaluation.evaluation_commitment,previous.sequence+1)
    new=make(RecoveryState,goal_id=goal.goal_id,active_plan_commitment=plan.plan_commitment,processed_request_ids=previous.processed_request_ids+(request.request_id,),completed_recovery_ids=previous.completed_recovery_ids+((candidate.candidate_id,) if not unsupported else ()),blocked_recovery_ids=previous.blocked_recovery_ids+((candidate.candidate_id,) if unsupported else ()),consumed_budget=previous.consumed_budget+1,uncertain_consumption=previous.uncertain_consumption,remaining_budget=previous.remaining_budget-1,reserved_capacity=previous.reserved_capacity,sequence=previous.sequence+1,history=previous.history+(core,),source_pin=previous.source_pin)
    verdict=RecoveryVerdict(goal.goal_id,'NOT_QUALIFIED' if unsupported else 'COORDINATION_RECORDED','NOT_ESTABLISHED','NO_EXECUTION_AUTHORITY')
    return new,evaluation,verdict
