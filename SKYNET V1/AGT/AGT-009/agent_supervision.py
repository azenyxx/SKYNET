"""Fail-closed supervision subset. No executor or lifecycle authority issuer.

Only observed post-execution terminal records are supported. RUNNING must be
host-pinned as an existing record; this module cannot establish its authority.
Other transitions remain NOT_QUALIFIED. No durable replay or active cancellation.
"""
from agent_supervision_contracts import *


def supervise(recovery_arguments, previous, request, authorization, policy,
              *, expected_state, expected_source, approved_authorizations,
              expected_policy, observation_sequence, stop=False, now=0, deadline=1):
    for obj, cls in ((previous, SupervisionState), (request, TransitionRequest),
                     (authorization, TransitionAuthorization), (policy, SupervisionPolicy)):
        need(type(obj) is cls, 'CONTRACT')
        obj.__post_init__()
    recovery.feedback.planning.memory.guard(stop, now, deadline, previous.remaining_budget, 0)
    need(expected_state == previous.state_commitment == request.source_state_commitment, 'STALE_STATE')
    need(expected_source == digest(recovery_arguments), 'SOURCE_PIN')
    need(expected_policy == policy.policy_commitment, 'POLICY_PIN')
    need(type(approved_authorizations) is tuple and len(approved_authorizations) <= 16, 'HOST_PINS')
    need(authorization.authorization_commitment in approved_authorizations, 'AUTHORIZATION')
    need(authorization.request_commitment == request.request_commitment, 'REQUEST_BINDING')
    need(request.actor_id == authorization.authorized_actor == previous.agent.agent_id, 'ACTOR')
    edge = (request.source_status, request.target_status)
    need(edge == authorization.approved_transition and edge in policy.allowed_transitions, 'TRANSITION')
    need(request.source_status == previous.agent.status, 'SOURCE_STATUS')
    need(request.request_id not in previous.processed_requests, 'REPLAY')
    integer(observation_sequence)
    need(observation_sequence == len(previous.processed_requests) + 1 <= 16, 'SEQUENCE')
    need(type(recovery_arguments) is tuple and len(recovery_arguments) == 7, 'SOURCE_SHAPE')
    result = recovery.coordinate(*recovery_arguments)
    source = recovery_arguments[0]
    goal, plan = source[:2]
    workflow = previous.active_workflow
    need(workflow.goal_id == goal.goal_id and workflow.plan_commitment == plan.plan_commitment, 'WORKFLOW')
    outcomes = source[4][2][1].task_outcomes
    statuses = tuple((item.task_id, item.execution_status) for item in outcomes)
    need(workflow.task_statuses == statuses, 'TASK_EVIDENCE')
    task = next((t for t in source[2][2] if t.task_id == previous.agent.current_task), None)
    need(task is not None and task.agent_id == previous.agent.agent_id, 'TASK_AGENT')
    bundle = source[2][6][task.task_id]
    need(previous.agent.approved_capabilities == bundle[0].capabilities, 'CAPABILITIES')
    balances = (previous.confirmed_consumption, previous.uncertain_consumption,
                previous.reserved_capacity, previous.remaining_budget)
    rs = result[0]
    need(balances == (rs.consumed_budget, rs.uncertain_consumption,
                     rs.reserved_capacity, rs.remaining_budget), 'ACCOUNTING')
    need(sum(balances) == goal.resource_budget and goal.resource_budget <= policy.resource_ceiling, 'CEILING')
    supported = request.target_status in ('COMPLETED', 'FAILED', 'UNCERTAIN', 'BLOCKED')
    if not supported:
        return previous, make(SupervisionVerdict, transition_status='NOT_QUALIFIED',
                              reason_code='NO_QUALIFIED_LIFECYCLE_EVIDENCE', verification_status='NOT_ESTABLISHED')
    need(dict(statuses)[task.task_id] == request.target_status, 'FALSE_COMPLETION')
    if request.target_status == 'COMPLETED':
        need(all(dict(statuses)[dep] == 'COMPLETED' for dep in task.dependencies), 'DEPENDENCY')
    agent = make(AgentLifecycle, agent_id=previous.agent.agent_id,
                 status=request.target_status, approved_capabilities=previous.agent.approved_capabilities,
                 current_task=previous.agent.current_task)
    observation = make(SupervisionObservation, observation_id=request.request_id,
                       source_component='AGT008', source_commitment=digest(result),
                       observed_status=result[2].execution_status, sequence=observation_sequence)
    state = make(SupervisionState, active_workflow=workflow, agent=agent,
                 processed_requests=previous.processed_requests + (request.request_id,),
                 confirmed_consumption=balances[0], uncertain_consumption=balances[1],
                 reserved_capacity=balances[2], remaining_budget=balances[3],
                 history=previous.history + ((previous.state_commitment, request.request_commitment,
                     authorization.authorization_commitment, observation.observation_commitment),))
    return state, make(SupervisionVerdict, transition_status='ALLOW_RECORD',
                       reason_code='OBSERVED_ONLY_NO_EXECUTION', verification_status='NOT_ESTABLISHED')
