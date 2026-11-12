"""Offline advisory feedback. No dispatch/replan/authorization API.
Source authenticity is a trusted-host assumption. No active cancellation or recovery.
AGT005 collaboration evidence is not independently ingested by this version.
"""
from agent_feedback_contracts import *

def initial(goal,policy):
    goal.__post_init__();policy.__post_init__()
    return make(FeedbackState,goal_id=goal.goal_id,processed_observation_ids=(),accepted_signal_ids=(),proposal_ids=(),consumed_budget=0,remaining_budget=policy.resource_ceiling)

def source_records(goal,plan,arguments,execution_host,result):
    """Validate original results without executing governance again."""
    need(plan==planning.build(goal,arguments,execution_host,plan.plan_version)[0],'PLAN_BINDING')
    need(type(result) is tuple and len(result)==3);state,verdict,raw=result
    need(type(state) is planning.PlanningState and type(verdict) is planning.PlanningVerdict);state.__post_init__();verdict.__post_init__()
    need(state.executed and state.goal_id==verdict.goal_id==goal.goal_id and verdict.plan_id==plan.plan_id and state.active_plan_commitment==plan.plan_commitment,'RESULT_BINDING')
    experiences=planning.memory.ingest_governance(arguments,raw)
    gs,trace,gv,actual=raw
    need(state.outcome_commitment==planning.digest((execution_host,raw)),'OUTCOME_BINDING')
    need((state.completed_task_ids,state.failed_task_ids,state.blocked_task_ids,state.consumed_budget,state.uncertain_consumption,state.reserved_consumption)==(gs.completed_tasks,gs.failed_tasks,gs.blocked_tasks,gs.confirmed_spend,gs.uncertain_spend,gs.reserved_capacity),'ACCOUNTING_BINDING')
    need(state.remaining_budget+state.consumed_budget+state.uncertain_consumption+state.reserved_consumption==goal.resource_budget,'CONSERVATION')
    need((verdict.execution_status,verdict.verification_status,verdict.reason_code)==(gv.execution_status,gv.verification_status,gv.reason_code),'VERDICT_BINDING')
    ids=tuple(t.task_id for t in plan.ordered_tasks);need(tuple(o.task_id for o in trace.task_outcomes)==ids,'TASK_SET')
    accepted={k for k,_ in actual};completed={o.task_id for o in trace.task_outcomes if o.execution_status=='COMPLETED'}
    need(completed<=accepted and completed==set(gs.completed_tasks),'FALSE_COMPLETION')
    need(all(o.execution_status=='COMPLETED' for o in trace.task_outcomes if o.task_id in gs.completed_tasks),'FALSE_COMPLETION')
    return trace.task_outcomes,experiences

def observe(goal,plan,arguments,execution_host,result,start=1):
    integer(start);need(start>0);outcomes,_=source_records(goal,plan,arguments,execution_host,result);pin=digest((goal,plan,arguments,execution_host,result))
    return tuple(make(ObservationRecord,observation_id='obs:'+digest((pin,o.task_id)),goal_id=goal.goal_id,task_id=o.task_id,source_component='AGT003_VIA_AGT006',source_commitment=pin,execution_status=o.execution_status,verification_status='NOT_ESTABLISHED',observed_sequence=start+i) for i,o in enumerate(outcomes))

def evaluate(goal,plan,arguments,execution_host,result,observations,policy,previous,host,*,stop=False,now=0,deadline=1):
    for obj,kind in ((policy,DecisionPolicy),(previous,FeedbackState),(host,HostPins)):
        need(type(obj) is kind);obj.__post_init__()
    planning.memory.guard(stop,now,deadline,previous.remaining_budget,0)
    need(host.goal_commitment==goal.goal_commitment and host.policy_commitment==policy.policy_commitment,'HOST_AUTHORITY');need(previous.goal_id==goal.goal_id and previous.state_commitment==host.expected_state,'STALE_STATE')
    need(previous.consumed_budget+previous.remaining_budget==policy.resource_ceiling,'BUDGET');need(previous.revision<4,'REVISION_LIMIT')
    need(type(observations) is tuple and 1<=len(observations)<=64,'COUNT');need(len(planning.mc.encoded(observations))<=16384,'CONTEXT_LIMIT')
    pin=digest((goal,plan,arguments,execution_host,result));need(pin in host.approved_sources,'UNAUTHORIZED_SOURCE')
    expected=observe(goal,plan,arguments,execution_host,result,len(previous.processed_observation_ids)+1)
    need(observations==expected,'OBSERVATION_BINDING');ids=tuple(o.observation_id for o in observations);refs(previous.processed_observation_ids+ids,64)
    planning.memory.guard(stop,now,deadline,previous.remaining_budget,len(ids))
    mapping={'COMPLETED':('TASK_COMPLETED','INFO'),'FAILED':('TASK_FAILED','WARNING'),'BLOCKED':('DEPENDENCY_BLOCKED','WARNING'),'UNCERTAIN':('EXECUTION_UNCERTAIN','CRITICAL'),'STOPPED':('STOP_REQUESTED','WARNING'),'DEADLINE':('DEADLINE_REACHED','WARNING'),'BUDGET_EXHAUSTED':('RESOURCE_PRESSURE','WARNING')}
    signals=tuple(make(FeedbackSignal,signal_id='signal:'+o.observation_id,observation_refs=(o.observation_id,),signal_type=mapping[o.execution_status][0],severity=mapping[o.execution_status][1],confidence_status='NOT_ESTABLISHED') for o in observations)
    refs(previous.accepted_signal_ids+tuple(s.signal_id for s in signals),32)
    group=lambda status:tuple(o.task_id for o in observations if o.execution_status==status)
    ps=result[0];progress=make(ProgressSnapshot,snapshot_id='progress:'+pin,goal_id=goal.goal_id,completed_task_ids=group('COMPLETED'),failed_task_ids=tuple(o.task_id for o in observations if o.execution_status in ('FAILED','STOPPED','DEADLINE','BUDGET_EXHAUSTED')),blocked_task_ids=group('BLOCKED'),uncertain_task_ids=group('UNCERTAIN'),consumed_budget=ps.consumed_budget,remaining_budget=ps.remaining_budget,uncertain_consumption=ps.uncertain_consumption)
    deviations=tuple(sorted({o.execution_status for o in observations if o.execution_status!='COMPLETED'}))
    assessment=make(DeviationAssessment,assessment_id='assessment:'+pin,goal_id=goal.goal_id,plan_commitment=plan.plan_commitment,expected_outcomes=tuple((t.task_id,'COMPLETED') for t in plan.ordered_tasks),observed_outcomes=tuple((o.task_id,o.execution_status) for o in observations),deviation_codes=deviations,observation_refs=ids)
    desired='ESCALATE' if deviations else 'NO_ACTION';decision=desired if desired in policy.allowed_decisions else 'NO_ACTION';need(decision in policy.allowed_decisions,'DECISION_DENIED')
    proposals=()
    if decision=='ESCALATE':
        need(policy.max_proposals>=1,'PROPOSAL_LIMIT');proposal=make(CorrectiveProposal,proposal_id='proposal:'+pin,goal_id=goal.goal_id,proposal_type='ESCALATE_TO_HOST',affected_task_ids=tuple(o.task_id for o in observations if o.execution_status!='COMPLETED'),required_authorization='TRUSTED_HOST_APPROVAL',estimated_cost=0,observation_refs=ids);proposals=(proposal,)
    proposal_ids=tuple(p.proposal_id for p in proposals);refs(previous.proposal_ids+proposal_ids,8)
    history=previous.history+((previous.state_commitment,digest(host),pin,digest((observations,signals,progress,assessment,proposals)),len(ids)),)
    new=make(FeedbackState,goal_id=goal.goal_id,processed_observation_ids=previous.processed_observation_ids+ids,accepted_signal_ids=previous.accepted_signal_ids+tuple(s.signal_id for s in signals),proposal_ids=previous.proposal_ids+proposal_ids,consumed_budget=previous.consumed_budget+len(ids),remaining_budget=previous.remaining_budget-len(ids),history=history,revision=previous.revision+1)
    verdict=FeedbackVerdict(goal.goal_id,decision,'NOT_ESTABLISHED','HOST_REVIEW_ONLY')
    return new,signals,progress,assessment,proposals,verdict
