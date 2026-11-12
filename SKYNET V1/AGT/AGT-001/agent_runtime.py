"""Trusted host supplies grants separately from agent data. Not a sandbox for host code.
No persistence; boundary signals are untrusted telemetry. COG019 NOT_QUALIFIED.
Inherited COG debt remains open; C20-003 fixed only in historical tested R1 path.
"""
from dataclasses import replace
from agent_contracts import *
COG019_STATUS='NOT_QUALIFIED'
EDGES=(('CREATED','VALIDATED'),('VALIDATED','PLANNED'),('PLANNED','AUTHORIZED'),('AUTHORIZED','EXECUTING'),('EXECUTING','OBSERVING'),('OBSERVING','EXECUTING'),('OBSERVING','EVALUATING'),('EVALUATING','COMPLETED'))
def transition(state,status,completed=None,budget=None,last=None):
    state.__post_init__();need(state.current_status not in TERMINAL,'TERMINAL')
    need((state.current_status,status) in EDGES or status in TERMINAL[1:],'TRANSITION')
    need(status!='COMPLETED','COMPLETION_REQUIRES_OBSERVATIONS')
    return replace(state,current_status=status,completed_actions=state.completed_actions if completed is None else completed,remaining_budget=state.remaining_budget if budget is None else budget,last_observation_id=state.last_observation_id if last is None else last,transition_count=state.transition_count+1)
def finish(state,plan,observations):
    need(state.current_status=='EVALUATING');need(tuple(o.action_id for o in observations)==tuple(a.action_id for a in plan.actions),'MISSING_OBSERVATION')
    for a,o in zip(plan.actions,observations):
        o.__post_init__();need(o.execution_status=='SUCCESS' and o.input_commitment==digest('action',a))
    need(state.completed_actions==tuple(a.action_id for a in plan.actions))
    return replace(state,current_status='COMPLETED',transition_count=state.transition_count+1)
def plan(task,candidates):
    task.__post_init__();need(type(candidates) is tuple and 0<len(candidates)<=task.max_actions,'ACTION_COUNT')
    for a in candidates:
        need(type(a) is AgentAction);a.__post_init__();need(a.task_id==task.task_id,'CROSS_TASK');need(a.action_type in task.allowed_actions,'ACTION_DENIED')
    refs(tuple(a.action_id for a in candidates));pending={a.action_id:a for a in candidates};ordered=[];depth={}
    need(all(set(a.dependencies)<=set(pending) for a in candidates),'MISSING_DEPENDENCY')
    while pending:
        ready=sorted(k for k,a in pending.items() if set(a.dependencies)<=set(depth));need(bool(ready),'CYCLE')
        for k in ready:
            a=pending.pop(k);depth[k]=1+max((depth[x] for x in a.dependencies),default=0);need(depth[k]<=task.max_depth,'DEPTH');ordered.append(a)
    commitment=digest('plan',(task.task_id,tuple(ordered)))
    return AgentPlan('p:'+commitment,task.task_id,tuple(ordered),commitment)
def dispatch(action,context):
    key,value=action.input_payload
    if action.action_type=='READ_CONTEXT':need(key=='context');return context
    if action.action_type=='TRANSFORM':
        need(key in ('UPPER','LOWER','LENGTH'),'TRANSFORM_DENIED');return value.upper() if key=='UPPER' else value.lower() if key=='LOWER' else len(value)
    if action.action_type=='EVALUATE':need(key in ('NONEMPTY','ASCII'),'CONDITION_DENIED');return bool(value) if key=='NONEMPTY' else value.isascii()
    if action.action_type=='RECORD':need(key=='diagnostic');return value
    raise Invalid('UNKNOWN_HANDLER')
def execute(identity,task,candidates,context,grants,signals):
    need(type(identity) is AgentIdentity and type(task) is AgentTask);identity.__post_init__();task.__post_init__()
    need(type(context) is str);plain(context);need(type(signals) is tuple and 1<=len(signals)<=65)
    previous=-1
    for stop,now in signals:need(type(stop) is bool);integer(now);need(now>=previous);previous=now
    state=AgentState(task.task_id,'CREATED',(),task.max_budget,'',0);events=[];observations=[]
    def move(status,**kwargs):
        nonlocal state
        old=state;state=transition(state,status,**kwargs);events.append((old.current_status,status,state.transition_count))
    reason='OK'
    try:
        need(identity.agent_id==task.agent_id,'AGENT_MISMATCH');need(task.input_commitment==digest('context',context),'INPUT_BINDING');move('VALIDATED')
        p=plan(task,candidates);move('PLANNED')
        need(type(grants) is tuple and len(grants)<=64,'GRANTS')
        for g in grants:need(type(g) is AuthorizationGrant);g.__post_init__()
        refs(tuple(g.authorization_id for g in grants));matches=[g for g in grants if g.authorization_id==task.authorization_id];need(len(matches)==1,'NO_AUTHORITY');g=matches[0]
        need((g.task_id,g.agent_id,g.task_commitment,g.candidate_commitment)==(task.task_id,identity.agent_id,digest('task',task),digest('candidates',candidates)),'GRANT_BINDING');need(task.max_budget<=g.max_budget,'GRANT_BUDGET')
        need(all(a.required_capability in identity.capability_ids for a in p.actions),'CAPABILITY');need(len(signals)>=len(p.actions),'SIGNALS');move('AUTHORIZED')
        for i,a in enumerate(p.actions):
            stop,now=signals[i]
            if stop:reason='STOP';move('STOPPED');break
            if now>=task.deadline:reason='DEADLINE';move('DEADLINE');break
            if state.remaining_budget<1:reason='BUDGET';move('BUDGET_EXHAUSTED');break
            need(set(a.dependencies)<=set(state.completed_actions));move('EXECUTING')
            try:output=dispatch(a,context);plain(output);success=True
            except Exception:output=None;success=False
            ic=digest('action',a);oc=digest('output',output);oid='o:'+digest('observation',(task.task_id,a.action_id,ic,oc,success))
            o=AgentObservation(oid,a.action_id,'SUCCESS' if success else 'FAILED',ic,oc,(oid,),1,'DIAGNOSTIC' if success else 'HANDLER_FAILED');observations.append(o)
            move('OBSERVING',completed=state.completed_actions+((a.action_id,) if success else ()),budget=state.remaining_budget-1,last=oid)
            if not success:reason='HANDLER_FAILED';move('FAILED');break
        if state.current_status=='OBSERVING':
            move('EVALUATING');old=state;state=finish(state,p,tuple(observations));events.append((old.current_status,'COMPLETED',state.transition_count))
    except Invalid as e:
        reason=str(e);move('REJECTED')
    tc=digest('trace',(task.task_id,tuple(events),tuple(observations)))
    trace=AgentExecutionTrace('t:'+tc,task.task_id,tuple(events),tuple(observations),tc)
    verdict=AgentVerdict(task.task_id,state.current_status,'LOCAL_COMPLETE' if state.current_status=='COMPLETED' else 'INCOMPLETE','NOT_ESTABLISHED',reason)
    return state,trace,verdict

def replay_equal(first,second):return first==second
