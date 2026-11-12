"""Bounded planning; host pins are authoritative assumptions, not signatures.
Post-execution replanning is intentionally NOT_QUALIFIED, always rejected.
No IO, new grants, natural-language interpretation, recovery or active cancellation.
Inherited AGT/COG findings remain open.
"""
from agent_planning_contracts import *
import agent_governance as gov
import agent_memory as memory
import agent_collaboration as collaboration

def validate_source(goal,arguments,host):
    need(type(goal) is AgentGoal and type(host) is HostApproval);goal.__post_init__();host.__post_init__()
    need(host.goal_commitment==goal.goal_commitment,'GOAL_AUTHORITY')
    need(type(arguments) is tuple and len(arguments)==9,'SOURCE');need(digest(arguments) in host.source_commitments,'SOURCE_AUTHORITY')
    need(arguments[4].owner_id==goal.owner_agent_id,'OWNER');need(arguments[1].global_budget<=goal.resource_budget,'BUDGET')
    need(len(arguments[5])<=8,'AGENT_LIMIT')
    schedule,prepared=gov.prepare(*arguments[:7])
    for meta,bundle,plan in prepared.values():need(all(a.required_capability in goal.authorized_capabilities for a in plan.actions),'CAPABILITY')
    return schedule,prepared

def build(goal,arguments,host,version=0):
    integer(version);need(version<=4,'REVISION_LIMIT');schedule,prepared=validate_source(goal,arguments,host);tasks=[]
    for k in schedule.ordered_task_ids:
        meta,bundle,p=prepared[k]
        tasks.append(make(PlanTask,task_id=k,goal_id=goal.goal_id,assigned_agent_id=meta.agent_id,required_capabilities=tuple(sorted({a.required_capability for a in p.actions})),dependency_ids=meta.dependencies,estimated_cost=meta.allocated_budget,source_task_commitment=meta.task_commitment))
    tasks=tuple(tasks);links=tuple((d,t.task_id) for t in tasks for d in t.dependency_ids);total=sum(t.estimated_cost for t in tasks)
    need(total<=goal.resource_budget and total<=arguments[1].global_budget,'INSUFFICIENT_BUDGET')
    plan=make(ExecutionPlan,plan_id='plan:'+digest((goal,arguments,version)),goal_id=goal.goal_id,ordered_tasks=tasks,dependency_edges=links,total_estimated_cost=total,plan_version=version,goal_commitment=goal.goal_commitment,source_commitment=digest(arguments))
    decomposition=make(GoalDecomposition,decomposition_id='decomp:'+plan.plan_commitment,goal_id=goal.goal_id,subgoal_ids=tuple(t.task_id for t in tasks),dependency_edges=links)
    evaluation=make(PlanEvaluation,evaluation_id='eval:'+plan.plan_commitment,plan_id=plan.plan_id,feasibility_status='FEASIBLE',constraint_violations=(),resource_projection=total)
    return plan,decomposition,evaluation

def initial(goal,plan):
    goal.__post_init__();plan.__post_init__();need(plan.goal_commitment==goal.goal_commitment)
    return make(PlanningState,goal_id=goal.goal_id,active_plan_commitment=plan.plan_commitment,completed_task_ids=(),failed_task_ids=(),blocked_task_ids=(),consumed_budget=0,remaining_budget=goal.resource_budget,revision_count=plan.plan_version)

def check(goal,plan,state,host):
    need(type(state) is PlanningState and type(plan) is ExecutionPlan and type(host) is HostApproval);state.__post_init__();plan.__post_init__();host.__post_init__();goal.__post_init__()
    need(host.goal_commitment==plan.goal_commitment==goal.goal_commitment,'GOAL_BINDING');need(state.goal_id==plan.goal_id==goal.goal_id)
    need(state.active_plan_commitment==plan.plan_commitment and state.state_commitment==host.expected_state,'STALE_STATE');need(state.revision_count==plan.plan_version)
    need(state.consumed_budget+state.uncertain_consumption+state.reserved_consumption+state.remaining_budget==goal.resource_budget,'CONSERVATION')

def execute(goal,plan,state,arguments,host,*,stop=False,now=0,deadline=1):
    check(goal,plan,state,host);memory.guard(stop,now,deadline,state.remaining_budget,0)
    need(not state.executed,'RETRY_DISABLED');need(plan.plan_commitment in host.execution_plans,'EXECUTION_AUTHORITY')
    need(plan==build(goal,arguments,host,plan.plan_version)[0],'PLAN_BINDING');need(plan.total_estimated_cost<=state.remaining_budget,'BUDGET')
    result=gov.govern(*arguments);s,t,v,raw=result
    # Exact actual predecessor result is returned, not replaced by a success assertion.
    new=make(PlanningState,goal_id=goal.goal_id,active_plan_commitment=plan.plan_commitment,completed_task_ids=s.completed_tasks,failed_task_ids=s.failed_tasks,blocked_task_ids=s.blocked_tasks,consumed_budget=s.confirmed_spend,remaining_budget=goal.resource_budget-s.confirmed_spend-s.uncertain_spend-s.reserved_capacity,revision_count=plan.plan_version,uncertain_consumption=s.uncertain_spend,reserved_consumption=s.reserved_capacity,executed=True,outcome_commitment=digest((host,result)))
    verdict=PlanningVerdict(goal.goal_id,plan.plan_id,v.execution_status,v.verification_status,v.reason_code)
    return new,verdict,result

def revise(goal,plan,state,new_arguments,host,reason,*,stop=False,now=0,deadline=1):
    check(goal,plan,state,host);memory.guard(stop,now,deadline,state.remaining_budget,0)
    need(not state.executed,'POST_EXECUTION_REVISION_NOT_QUALIFIED');need(state.revision_count<4,'REVISION_LIMIT')
    need(digest((state.state_commitment,plan.plan_commitment,digest(new_arguments),reason)) in host.revision_approvals,'REVISION_AUTHORITY')
    new=build(goal,new_arguments,host,plan.plan_version+1)[0];need(new.total_estimated_cost<=state.remaining_budget,'BUDGET')
    revision=make(PlanRevision,revision_id='revision:'+new.plan_commitment,previous_plan_commitment=plan.plan_commitment,new_plan_commitment=new.plan_commitment,revision_reason=reason,affected_task_ids=tuple(t.task_id for t in new.ordered_tasks),authorization_commitment=digest(host))
    return new,initial(goal,new),revision

def diagnostic_context(goal,plan,state,host,exchange_arguments,previous,*,stop=False,now=0,deadline=1):
    check(goal,plan,state,host);memory.guard(stop,now,deadline,state.remaining_budget,0)
    need(digest((exchange_arguments,previous)) in host.context_approvals,'CONTEXT_AUTHORITY')
    return collaboration.exchange(*exchange_arguments,previous=previous,stop=stop,now=now,deadline=deadline)

def replay_equal(a,b):return digest(a)==digest(b)
