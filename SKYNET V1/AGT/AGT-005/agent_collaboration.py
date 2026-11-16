"""Pure bounded context exchange. No IO, task dispatch, recovery or authority promotion.
Handoffs are assignment-only and require an existing separate target authorization.
HostPolicy and Memory HostAccess must come from the trusted host boundary.
"""
from agent_collaboration_contracts import *
import agent_memory as memory

def exchange(session,grant,host,store,scope,sender_access,recipient_access,messages,*,previous,stop=False,now=0,deadline=1):
    """Validate complete batch before returning any payload. One operation per message.
    Rejected batch raises Invalid and commits nothing. Replay protection is not durable.
    Same scope may explicitly authorize both agents; no scope widening is performed.
    """
    for obj,kind in ((session,CollaborationSession),(grant,CollaborationGrant),(host,HostPolicy),(store,m.MemoryState),(scope,m.MemoryScope),(sender_access,m.HostAccess),(recipient_access,m.HostAccess)):
        need(type(obj) is kind,'CONTRACT');obj.__post_init__()
    need(type(messages) is tuple and len(messages)<=64,'MESSAGE_LIMIT')
    check_state(session,host,previous);memory.guard(stop,now,deadline,previous.remaining_budget,len(messages))
    need(session.session_commitment==host.session_commitment and grant.grant_commitment in host.grant_commitments,'HOST_AUTHORIZATION')
    need(store.state_commitment==host.memory_state_commitment,'STALE_MEMORY')
    need(sender_access.authorization_commitment in host.access_commitments and recipient_access.authorization_commitment in host.access_commitments,'ACCESS_PIN')
    need(grant.issuer_id==session.owner_id and grant.sender_agent_id in session.participant_agent_ids and grant.recipient_agent_id in session.participant_agent_ids,'PARTICIPANTS')
    need(scope.owner_agent_id==grant.sender_agent_id,'SOURCE_OWNER')
    need('TRANSFER' in grant.allowed_operations,'OPERATION_DENIED');need(len(previous.ordered_message_ids)+len(messages)<=min(64,grant.max_messages),'MESSAGE_LIMIT')
    ids=list(previous.ordered_message_ids);events=[];sources=[];delivered=[];state=previous
    for position,pair in enumerate(messages,len(previous.ordered_message_ids)+1):
        memory.guard(stop,now,deadline,state.remaining_budget,1)
        need(type(pair) is tuple and len(pair)==2);message,payload=pair;need(type(message) is AgentMessage);message.__post_init__()
        need(type(payload) is str and len(payload.encode('utf-8'))<=4096,'PAYLOAD_LIMIT')
        need(message.payload_commitment==m.digest('content',payload),'PAYLOAD_COMMITMENT')
        need(message.session_id==session.session_id and message.sender_agent_id==grant.sender_agent_id and message.recipient_agent_id==grant.recipient_agent_id,'MESSAGE_BINDING')
        need(message.source_task_id in session.authorized_task_ids and message.source_task_id in grant.allowed_task_ids,'TASK_DENIED')
        need(message.message_id not in ids,'DUPLICATE_MESSAGE');need(message.sequence_number==position,'SEQUENCE')
        need(len(message.source_refs)==1 and set(message.source_refs)<=set(grant.allowed_memory_refs),'MEMORY_DENIED')
        contexts=[]
        for agent,access in ((message.sender_agent_id,sender_access),(message.recipient_agent_id,recipient_access)):
            query=m.MemoryQuery('query:'+message.message_id,agent,message.source_task_id,scope.scope_id,(),1,16384,access.authorization_ref,record_ids=message.source_refs)
            result=memory.retrieve(store,scope,query,access,stop=stop,now=now,deadline=deadline)
            need(result.record_ids==message.source_refs,'MISSING_OR_INVALIDATED_MEMORY')
            contexts.append(memory.assemble(store,scope,query,access,result,stop=stop,now=now,deadline=deadline))
        need(contexts[0].context==contexts[1].context,'CONTEXT_BINDING');record,content,experience=contexts[0].context[0]
        need(content==payload and record.source_task_id==message.source_task_id,'SOURCE_BINDING')
        transfer_id='transfer:'+message.message_id
        transfer=ContextTransfer(transfer_id,message.sender_agent_id,message.recipient_agent_id,message.source_refs,scope.scope_commitment,scope.scope_commitment,digest((transfer_id,message.sender_agent_id,message.recipient_agent_id,message.source_refs,scope.scope_commitment,scope.scope_commitment,'agt005-v1')))
        state,event=commit(session,host,state,'MESSAGE',message.message_id,digest((message,transfer,host,grant)),message.sequence_number);events.append(event)
        ids.append(message.message_id);sources.append(m.digest('entry',contexts[0].context[0]));delivered.append(contexts[1])
    trace=seal(CollaborationTrace,trace_id='trace:'+digest((session,grant,host,tuple(events),state)),session_id=session.session_id,ordered_events=tuple(events),source_commitments=tuple(sources))
    verdict=CollaborationVerdict(session.session_id,'DIAGNOSTIC_DELIVERED' if ids else 'EMPTY','NOT_ESTABLISHED','LOCAL_DIAGNOSTIC')
    return state,trace,verdict,tuple(delivered)

def initial(session):
    session.__post_init__()
    return seal(CollaborationState,session_id=session.session_id,ordered_message_ids=(),completed_handoffs=(),rejected_operations=(),consumed_budget=0,remaining_budget=session.session_budget,session_pin=session.session_commitment)

def check_state(session,host,state):
    need(type(state) is CollaborationState and type(host) is HostPolicy,'STATE_REQUIRED');state.__post_init__();host.__post_init__();session.__post_init__()
    need(state.state_commitment==host.expected_state,'STALE_OR_FORGED_STATE')
    need(state.session_id==session.session_id and state.session_pin==session.session_commitment==host.session_commitment,'SESSION_BINDING')
    need(state.consumed_budget+state.remaining_budget==session.session_budget,'CONSERVATION')

def commit(session,host,old,kind,op_id,pin,sequence,assignment=None):
    need(old.remaining_budget>=1,'OPERATION_BUDGET');ident(op_id);hashcheck(pin)
    core=(old.state_commitment,session.session_commitment,digest(host),kind,op_id,sequence,1,pin)
    messages=old.ordered_message_ids+((op_id,) if kind=='MESSAGE' else ())
    handoffs=old.completed_handoffs+((op_id,) if kind=='HANDOFF' else ())
    state=seal(CollaborationState,session_id=session.session_id,ordered_message_ids=messages,completed_handoffs=handoffs,rejected_operations=old.rejected_operations,consumed_budget=old.consumed_budget+1,remaining_budget=old.remaining_budget-1,history=old.history+(core,),assignments=old.assignments+((assignment,) if assignment else ()),session_pin=session.session_commitment)
    return state,core+(state.state_commitment,)

def handoff(session=None,host=None,previous=None,request=None,source=None,target=None,statuses=None,*,stop=False,now=0,deadline=1):
    """Source/target are actual seven-argument governance preflight snapshots.
    Host pins all snapshots and current dependency statuses. No task execution.
    A caller cannot create approval by constructing a TaskHandoff DTO.
    """
    need(session is not None,'DENIED');check_state(session,host,previous)
    memory.guard(stop,now,deadline,previous.remaining_budget,1)
    need(type(request) is TaskHandoff,'DENIED');request.__post_init__();need(request.handoff_status=='READY','DENIED')
    need(type(source) is tuple and len(source)==7 and type(target) is tuple and len(target)==7,'DENIED')
    approval=digest((request,source,target,statuses));need(approval in host.handoff_approvals,'DENIED')
    sp,sm=memory.gov.prepare(*source);tp,tm=memory.gov.prepare(*target)
    need(source[4].owner_id==target[4].owner_id==session.owner_id,'DENIED')
    k=request.task_id;need(k in sm and k in tm and k in session.authorized_task_ids,'DENIED')
    st,sb,splan=sm[k];tt,tb,tplan=tm[k]
    need(request.source_agent_id==st.agent_id and request.target_agent_id==tt.agent_id and st.agent_id!=tt.agent_id,'DENIED')
    need(st.agent_id in session.participant_agent_ids and tt.agent_id in session.participant_agent_ids,'DENIED')
    need(request.parent_authorization_ref==sb[4][0].authorization_id,'DENIED')
    need(k not in tuple(a[0] for a in previous.assignments) and request.handoff_id not in previous.completed_handoffs,'ALREADY_ASSIGNED')
    need(len(previous.completed_handoffs)<16,'HANDOFF_LIMIT')
    # Task agent/authorization IDs must differ; all task semantics must be identical.
    semantic=lambda t:tuple((f.name,getattr(t,f.name)) for f in fields(t) if f.name not in ('agent_id','authorization_id'))
    need(semantic(sb[1])==semantic(tb[1]) and sb[2]==tb[2] and sb[3]==tb[3] and st.dependencies==tt.dependencies,'TASK_OR_BUDGET_ESCALATION')
    need(type(statuses) is tuple and len(statuses)==len(sm),'BLOCKED_DEPENDENCY');refs(tuple(x[0] for x in statuses),16)
    status=dict(statuses);need(set(status)==set(sm),'BLOCKED_DEPENDENCY')
    need(all(x in ('READY','COMPLETED','FAILED','UNCERTAIN','BLOCKED') for x in status.values()),'DENIED')
    need(status[k]=='READY','DENIED')
    need(not any(status[d] in ('FAILED','UNCERTAIN') for d in st.dependencies),'FAILED_DEPENDENCY')
    need(all(status[d]=='COMPLETED' for d in st.dependencies),'BLOCKED_DEPENDENCY')
    need(source[1].failure_mode!='FAIL_STOP' or not any(v in ('FAILED','UNCERTAIN') for v in status.values()),'FAILED_DEPENDENCY')
    state,event=commit(session,host,previous,'HANDOFF',request.handoff_id,approval,previous.consumed_budget+1,(k,st.agent_id,tt.agent_id,st.task_commitment,tt.task_commitment))
    return state,event,request

def replay_equal(left,right):
    return digest(left)==digest(right)
