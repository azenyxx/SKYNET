"""Bounded governance; single-level host delegation and zero retries.
Inherited A01-001..003, A02-001..002 and COG findings remain OPEN.
Local reexecution shares AGT001 handlers; not independent verification.
No persistence, reconciliation, active interruption, or exactly-once guarantee.
"""
from dataclasses import replace
import agent_contracts as ac
import agent_runtime as ar
import agent_orchestrator as ao
import agent_orchestration_contracts as oc
from agent_governance_contracts import *

def qualify_output(bundle,plan,result):
    cost=ao.accept(bundle,plan,result)
    # Recompute fixed pure handlers only; never invoke arbitrary supplied callbacks.
    for index,(action,obs) in enumerate(zip(plan.actions,result[1].observations)):
        stop,now=bundle[5][index];need(not stop and now<bundle[1].deadline,'ACTION_AFTER_STOP')
        need(index<bundle[1].max_budget,'ACTION_OVER_BUDGET')
        try:output=ar.dispatch(action,bundle[3]);ac.plain(output);success=True
        except Exception:output=None;success=False
        need(obs.execution_status==('SUCCESS' if success else 'FAILED'),'SEMANTIC_STATUS')
        need(obs.output_commitment==ac.digest('output',output),'OUTPUT_MISMATCH')
        need(obs.reason_code==('DIAGNOSTIC' if success else 'HANDLER_FAILED'),'REASON')
    return cost

def prepare(request_id,policy,tasks,delegations,host,registry,bundles):
    ident(request_id);need(type(policy) is ExecutionPolicy and type(host) is HostAuthority);policy.__post_init__();host.__post_init__()
    need(host.request_id==request_id and host.policy_commitment==digest(policy),'HOST_BINDING')
    need(type(tasks) is tuple and 1<=len(tasks)<=policy.max_tasks and type(bundles) is tuple and len(bundles)==len(tasks))
    need(type(delegations) is tuple and len(delegations)==len(tasks));need(type(registry) is tuple and 1<=len(registry)<=16)
    for a in registry:need(type(a) is oc.SupervisedAgent);a.__post_init__()
    refs(tuple(a.agent_id for a in registry))
    for t in tasks:need(type(t) is DelegatedTask);t.__post_init__()
    refs(tuple(t.task_id for t in tasks))
    for d in delegations:need(type(d) is DelegationGrant);d.__post_init__()
    refs(tuple(d.delegation_id for d in delegations));need(set(digest(d) for d in delegations)==set(host.delegation_commitments),'HOST_APPROVAL')
    parents={g.authorization_id:g for g in host.parent_authorizations};dmap={d.delegation_id:d for d in delegations};metas=[];prepared={};used=set()
    for t,b in zip(tasks,bundles):
        need(t.delegation_id in dmap and t.delegation_id not in used,'DELEGATION_REUSE');used.add(t.delegation_id);d=dmap[t.delegation_id]
        need(d.issuer_id==host.owner_id and d.delegate_agent_id==t.agent_id and t.agent_id in host.approved_agent_ids,'DELEGATE')
        need(d.parent_authorization_id in parents,'PARENT');parent=parents[d.parent_authorization_id]
        need(d.allowed_task_ids==(t.task_id,) and parent.task_id==t.task_id and parent.agent_id==t.agent_id,'PARENT_SCOPE')
        need(set(d.allowed_capabilities)<=set(host.parent_capabilities),'CAPABILITY_ESCALATION');need(t.allocated_budget<=d.max_budget<=parent.max_budget,'BUDGET_ESCALATION')
        need(type(b) is tuple and len(b)==6 and b[4]==(parent,),'PARENT_GRANT');need(type(b[1]) is ac.AgentTask)
        need(t.allocated_budget==b[1].max_budget and t.task_commitment==parent.task_commitment,'TASK_SCOPE')
        meta=oc.OrchestratedTask(t.task_id,t.agent_id,t.dependencies,t.task_commitment,oc.digest(parent),t.allocated_budget);ap=ao.preflight(meta,b,registry)
        need(all(a.required_capability in d.allowed_capabilities for a in ap.actions),'DELEGATED_CAPABILITY')
        metas.append(meta);prepared[t.task_id]=(t,b,ap)
    req=oc.OrchestrationRequest(request_id,host.owner_id,tuple(t.task_id for t in tasks),policy.global_budget,policy.max_tasks,policy.max_depth)
    p=ao.schedule(req,tuple(metas));return p,prepared

def govern(request_id,policy,tasks,delegations,host,registry,bundles,signals,deadline):
    p,prepared=prepare(request_id,policy,tasks,delegations,host,registry,bundles)
    integer(deadline);need(type(signals) is tuple and len(signals)==len(tasks));previous=-1
    for s in signals:need(type(s) is tuple and len(s)==2 and type(s[0]) is bool);integer(s[1]);need(s[1]>=previous);previous=s[1]
    state=GovernanceState(request_id,(),(),(),p.ordered_task_ids,0,0,0,policy.global_budget,'RUNNING',policy.global_budget)
    decisions=[];outcomes=[];events=[];results=[];halt=None
    def accounting(k,kind):events.append((k,kind,state.confirmed_spend,state.reserved_capacity,state.uncertain_spend,state.remaining_available_budget))
    for i,k in enumerate(p.ordered_task_ids):
        task,bundle,ap=prepared[k];stop,now=signals[i];blocking=tuple(x for x in task.dependencies if x not in state.completed_tasks)
        if halt is None:
            if stop:halt='STOPPED'
            elif now>=deadline:halt='DEADLINE'
        reason=halt or ('PREREQUISITE_FAILED' if blocking else None)
        if reason is None and task.allocated_budget>state.remaining_available_budget:reason='BUDGET_EXHAUSTED'
        if reason:
            decisions.append(DependencyDecision(k,'BLOCKED' if blocking else 'NOT_RUN',False,blocking,reason));outcomes.append(TaskOutcome(k,'BLOCKED','NOT_ESTABLISHED',0,0,0,digest(('NOT_EXECUTED',k,reason)),reason));state=replace(state,pending_tasks=tuple(x for x in state.pending_tasks if x!=k),blocked_tasks=state.blocked_tasks+(k,));continue
        decisions.append(DependencyDecision(k,'SATISFIED',True,(),'AUTHORIZED'))
        allocation=task.allocated_budget
        state=replace(state,reserved_capacity=allocation,remaining_available_budget=state.remaining_available_budget-allocation);accounting(k,'RESERVE')
        try:
            result=ar.execute(*bundle);cost=qualify_output(bundle,ap,result);need(cost<=allocation,'ALLOCATION')
        except Exception:
            state=replace(state,reserved_capacity=0,uncertain_spend=state.uncertain_spend+allocation,failed_tasks=state.failed_tasks+(k,),pending_tasks=tuple(x for x in state.pending_tasks if x!=k));accounting(k,'UNCERTAIN')
            outcomes.append(TaskOutcome(k,'UNCERTAIN','NOT_ESTABLISHED',0,0,allocation,digest(('NO_ACCEPTED_RESULT',k)),'EXECUTION_OUTCOME_UNCERTAIN'))
            if policy.failure_mode=='FAIL_STOP':halt='FAIL_STOP'
            continue
        results.append((k,result));v=result[2]
        state=replace(state,reserved_capacity=0,confirmed_spend=state.confirmed_spend+cost,remaining_available_budget=state.remaining_available_budget+allocation-cost,pending_tasks=tuple(x for x in state.pending_tasks if x!=k),completed_tasks=state.completed_tasks+((k,) if v.execution_status=='COMPLETED' else ()),failed_tasks=state.failed_tasks+((k,) if v.execution_status!='COMPLETED' else ()));accounting(k,'CONFIRM')
        outcomes.append(TaskOutcome(k,v.execution_status,v.verification_status,cost,0,0,result[1].trace_commitment,v.reason_code,'LOCAL_REEXECUTION_CHECK'))
        if v.execution_status in ('STOPPED','DEADLINE'):halt=v.execution_status
        elif v.execution_status!='COMPLETED' and policy.failure_mode=='FAIL_STOP':halt='FAIL_STOP'
    final=halt if halt in ('STOPPED','DEADLINE') else 'COMPLETED' if len(state.completed_tasks)==len(tasks) else 'PARTIAL'
    state=replace(state,status=final);verdict=GovernanceVerdict(request_id,final,'LOCAL_COMPLETE' if final=='COMPLETED' else 'INCOMPLETE','NOT_ESTABLISHED','OK' if final=='COMPLETED' else 'INCOMPLETE_EXECUTION')
    binding=digest((request_id,policy,tasks,delegations,host,registry,bundles,signals,deadline,p,state,verdict))
    tc=digest((binding,tuple(decisions),tuple(outcomes),tuple(events)));trace=GovernanceTrace('trace:'+tc,request_id,tuple(decisions),tuple(outcomes),tc,binding,tuple(events))
    return state,trace,verdict,tuple(results)

def replay_equal(a,b):return a==b
