"""Sequential host supervision. Signals and grants require a trusted host.
No active interruption, durable recovery, or independent evidence verification.
Fail-stop policy: no independent tasks continue after a non-successful result.
"""
from dataclasses import replace
import agent_contracts as ac
import agent_runtime as ar
from agent_orchestration_contracts import *
EDGES=(('CREATED','VALIDATED'),('VALIDATED','PLANNED'),('PLANNED','AUTHORIZED'),('AUTHORIZED','RUNNING'),('RUNNING','EVALUATING'),('EVALUATING','COMPLETED'))
def advance(state,status):
    state.__post_init__();need(state.status not in FINAL,'TERMINAL');need((state.status,status) in EDGES or status in FINAL[1:],'TRANSITION')
    return replace(state,status=status,transition_count=state.transition_count+1)
def schedule(request,tasks):
    need(type(request) is OrchestrationRequest);request.__post_init__();need(type(tasks) is tuple and len(tasks)==len(request.task_ids))
    for t in tasks:need(type(t) is OrchestratedTask);t.__post_init__()
    refs(tuple(t.task_id for t in tasks));need(set(request.task_ids)=={t.task_id for t in tasks},'TASK_SET')
    pending={t.task_id:t for t in tasks};order=[];depth={}
    need(all(set(t.dependencies)<=set(pending) for t in tasks),'MISSING_DEPENDENCY')
    while pending:
        ready=sorted(k for k,t in pending.items() if set(t.dependencies)<=set(depth));need(bool(ready),'CYCLE')
        for k in ready:
            t=pending.pop(k);depth[k]=1+max((depth[x] for x in t.dependencies),default=0);need(depth[k]<=request.max_depth,'DEPTH');order.append(k)
    dc=digest(tuple(sorted(tasks,key=lambda t:t.task_id)));pc=digest((request.request_id,tuple(order),dc))
    return OrchestrationPlan('plan:'+pc,request.request_id,tuple(order),dc,pc)
def preflight(meta,bundle,registry):
    need(type(bundle) is tuple and len(bundle)==6,'BUNDLE')
    identity,task,candidates,context,grants,signals=bundle
    need(type(identity) is ac.AgentIdentity and type(task) is ac.AgentTask);identity.__post_init__();task.__post_init__()
    matches=[a for a in registry if a.agent_id==meta.agent_id];need(len(matches)==1,'UNKNOWN_AGENT');a=matches[0]
    need(identity.agent_id==task.agent_id==meta.agent_id and task.task_id==meta.task_id,'IDENTITY');need(meta.task_id in a.allowed_task_ids,'ASSIGNMENT');need(a.identity_commitment==digest(identity),'IDENTITY_COMMITMENT')
    need(meta.task_commitment==ac.digest('task',task) and meta.max_budget==task.max_budget,'TASK_BINDING');need(type(context) is str and task.input_commitment==ac.digest('context',context),'CONTEXT')
    need(type(grants) is tuple and len(grants)==1 and type(grants[0]) is ac.AuthorizationGrant,'GRANT');g=grants[0];g.__post_init__()
    need(meta.grant_commitment==digest(g),'GRANT_COMMITMENT');need((g.authorization_id,g.agent_id,g.task_id,g.task_commitment,g.candidate_commitment)==(task.authorization_id,task.agent_id,task.task_id,meta.task_commitment,ac.digest('candidates',candidates)),'GRANT_BINDING');need(task.max_budget<=g.max_budget,'BUDGET_GRANT')
    p=ar.plan(task,candidates);need(all(x.required_capability in identity.capability_ids for x in p.actions),'CAPABILITY')
    need(type(signals) is tuple and len(p.actions)<=len(signals)<=65,'SIGNALS');last=-1
    for s in signals:need(type(s) is tuple and len(s)==2 and type(s[0]) is bool);integer(s[1]);need(s[1]>=last);last=s[1]
    return p

def accept(bundle,approved,result):
    need(type(result) is tuple and len(result)==3,'RESULT');state,trace,verdict=result;task=bundle[1]
    for value,kind in ((state,ac.AgentState),(trace,ac.AgentExecutionTrace),(verdict,ac.AgentVerdict)):need(type(value) is kind);value.__post_init__()
    need(state.task_id==trace.task_id==verdict.task_id==task.task_id,'RESULT_ID');need(state.current_status==verdict.execution_status,'STATUS');need(trace.trace_id=='t:'+trace.trace_commitment,'TRACE_ID')
    obs=trace.observations;need(len(obs)<=len(approved.actions));done=[];cost=0;failed=False
    for a,o in zip(approved.actions,obs):
        need(not failed and o.action_id==a.action_id,'ORDER');need(set(a.dependencies)<=set(done),'DEPENDENCY');need(o.input_commitment==ac.digest('action',a),'ACTION_COMMITMENT');need(o.actual_cost==1,'COST')
        success=o.execution_status=='SUCCESS';expected='o:'+ac.digest('observation',(task.task_id,a.action_id,o.input_commitment,o.output_commitment,success));need(o.observation_id==expected and o.evidence_refs==(expected,),'OBSERVATION_BINDING')
        cost+=o.actual_cost
        if success:done.append(a.action_id)
        else:failed=True
    need(cost<=task.max_budget and state.remaining_budget==task.max_budget-cost,'ACCOUNTING');need(state.completed_actions==tuple(done),'COMPLETED_ACTIONS');need(state.last_observation_id==(obs[-1].observation_id if obs else ''),'LAST_OBSERVATION')
    events=[('CREATED','VALIDATED'),('VALIDATED','PLANNED'),('PLANNED','AUTHORIZED')];prev='AUTHORIZED'
    for o in obs:events.extend(((prev,'EXECUTING'),('EXECUTING','OBSERVING')));prev='OBSERVING'
    status=state.current_status
    if status=='COMPLETED':need(not failed and len(obs)==len(approved.actions),'FALSE_COMPLETED');events.extend(((prev,'EVALUATING'),('EVALUATING','COMPLETED')))
    else:
        need(status in ('STOPPED','DEADLINE','BUDGET_EXHAUSTED','FAILED'),'UNEXPECTED_RESULT')
        need((status=='FAILED')==failed,'FAILURE_STATUS');need(status=='FAILED' or len(obs)<len(approved.actions),'TERMINAL_CAUSE')
        if status=='BUDGET_EXHAUSTED':need(state.remaining_budget==0)
        if status in ('STOPPED','DEADLINE'):
            stop,now=bundle[5][len(obs)];need(stop if status=='STOPPED' else not stop and now>=task.deadline,'SIGNAL_CAUSE')
        events.append((prev,status))
    expected=tuple((a,b,i+1) for i,(a,b) in enumerate(events));need(trace.ordered_events==expected and state.transition_count==len(expected),'EVENTS')
    return cost

def supervise(request,tasks,registry,bundles,signals,deadline):
    p=schedule(request,tasks);need(type(registry) is tuple and len(registry)<=16);need(type(bundles) is tuple and len(bundles)==len(tasks));integer(deadline)
    for a in registry:need(type(a) is SupervisedAgent);a.__post_init__()
    refs(tuple(a.agent_id for a in registry));need(type(signals) is tuple and len(signals)==len(tasks));last=-1
    for s in signals:need(type(s) is tuple and len(s)==2 and type(s[0]) is bool);integer(s[1]);need(s[1]>=last);last=s[1]
    prepared={}
    for meta,bundle in zip(tasks,bundles):prepared[meta.task_id]=(meta,bundle,preflight(meta,bundle,registry))
    state=OrchestrationState(request.request_id,'CREATED',(),(),(),request.global_budget,0);events=[];records=[];outputs=[];status='COMPLETED';reason='OK'
    def move(s):
        nonlocal state
        old=state.status;state=advance(state,s);events.append((old,s,state.transition_count))
    for s in ('VALIDATED','PLANNED','AUTHORIZED','RUNNING'):move(s)
    for i,k in enumerate(p.ordered_task_ids):
        meta,bundle,ap=prepared[k];stop,now=signals[i]
        if stop:status='STOPPED';reason='STOP';break
        if now>=deadline:status='DEADLINE';reason='DEADLINE';break
        if meta.max_budget>state.remaining_budget:status='BUDGET_EXHAUSTED';reason='GLOBAL_BUDGET';break
        need(set(meta.dependencies)<=set(state.completed_tasks),'DEPENDENCY')
        try:
            result=ar.execute(*bundle);cost=accept(bundle,ap,result)
        except Exception:
            # Unknown accounting is never treated as free: retain full task ceiling.
            state=replace(state,remaining_budget=state.remaining_budget-meta.max_budget,failed_tasks=state.failed_tasks+(k,));records.append(TaskExecutionRecord(k,meta.agent_id,'FAILED',digest(('UNVERIFIED',k)),meta.max_budget,'SATISFIED','RESULT_UNVERIFIED'));status='FAILED';reason='RESULT_UNVERIFIED';break
        outputs.append(result);v=result[2];records.append(TaskExecutionRecord(k,meta.agent_id,v.execution_status,result[1].trace_commitment,cost,'SATISFIED',v.reason_code));state=replace(state,remaining_budget=state.remaining_budget-cost)
        if v.execution_status=='COMPLETED':state=replace(state,completed_tasks=state.completed_tasks+(k,))
        else:state=replace(state,failed_tasks=state.failed_tasks+(k,));status='PARTIAL';reason='TASK_NOT_COMPLETED';break
    remaining=tuple(k for k in p.ordered_task_ids if k not in state.completed_tasks+state.failed_tasks);state=replace(state,blocked_tasks=remaining)
    for k in remaining:
        m=prepared[k][0];records.append(TaskExecutionRecord(k,m.agent_id,'BLOCKED',digest(('NOT_EXECUTED',k)),0,'NOT_RUN',reason))
    if status=='COMPLETED':need(len(state.completed_tasks)==len(tasks));move('EVALUATING')
    move(status);v=OrchestrationVerdict(request.request_id,status,'LOCAL_COMPLETE' if status=='COMPLETED' else 'INCOMPLETE','NOT_ESTABLISHED',reason)
    binding=digest((request,p,tasks,registry,bundles,signals,deadline,state,v));tc=digest((binding,tuple(events),tuple(records)));trace=OrchestrationTrace('trace:'+tc,request.request_id,tuple(events),tuple(records),tc,binding)
    return state,trace,v,tuple(outputs)
