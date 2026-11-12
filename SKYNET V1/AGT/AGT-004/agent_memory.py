"""Pure in-memory snapshots. No IO, promotion, independent provenance or recovery.
Total retained records (including tombstones) <=256; no eviction/restoration.
HostAccess is a trust assumption, not authentication. Original AGT/COG debt remains.
Boundary STOP/deadline errors are explicit and preserve input state.
"""
from agent_memory_contracts import *
import agent_governance as gov

def guard(stop,now,deadline,budget,required):
    need(type(stop) is bool);integer(now);integer(deadline);integer(budget)
    need(not stop,'STOPPED');need(now<deadline,'DEADLINE');need(budget>=required,'OPERATION_BUDGET')
def authorize(scope,agent,task,ref,host,operation):
    need(type(scope) is MemoryScope and type(host) is HostAccess,'AUTHORITY_REQUIRED');scope.__post_init__();host.__post_init__()
    need((agent,task,ref,scope.scope_commitment)==(host.agent_id,host.task_id,host.authorization_ref,host.scope_commitment),'AUTHORIZATION_BINDING')
    need(agent in scope.allowed_agent_ids and task in scope.allowed_task_ids,'SCOPE');need(operation in scope.allowed_operations and operation in host.allowed_operations,'OPERATION_DENIED')
def empty(store_id='store'):
    return make(MemoryState,'state_commitment','state',store_id=store_id,record_count=0,active_record_ids=(),invalidated_record_ids=(),sequence_number=0,entries=())
def snapshot(old,entries,active,invalid,sequence):
    return make(MemoryState,'state_commitment','state',store_id=old.store_id,record_count=len(entries),active_record_ids=tuple(sorted(active)),invalidated_record_ids=tuple(sorted(invalid)),sequence_number=sequence,entries=entries)
def write(state,scope,request,host,experience,*,stop=False,now=0,deadline=1,budget=1024):
    need(type(state) is MemoryState and type(request) is MemoryWriteRequest);guard(stop,now,deadline,budget,1+state.record_count);state.__post_init__();request.__post_init__()
    authorize(scope,request.agent_id,request.task_id,request.authorization_ref,host,'WRITE');need(request.scope_id==scope.scope_id)
    need(type(experience) is ExperienceRecord);experience.__post_init__();need(experience.experience_commitment in host.source_commitments,'UNAPPROVED_SOURCE');need(experience.agent_id==scope.owner_agent_id,'OWNER');need(experience.task_id in host.source_task_ids and experience.task_id in scope.allowed_task_ids,'SOURCE_TASK');need(request.source_refs==experience.observation_refs and bool(request.source_refs),'SOURCE_REFS')
    need(state.record_count<256,'CAPACITY');need(all(r.memory_id!=request.request_id for r,_,_ in state.entries),'DUPLICATE_RECORD')
    seq=state.sequence_number+1
    record=MemoryRecord(request.request_id,scope.owner_agent_id,experience.task_id,request.source_refs[0],digest('content',request.content),request.content_type,'DIAGNOSTIC',seq,scope.scope_commitment,request.source_refs)
    return snapshot(state,state.entries+((record,request.content,experience),),state.active_record_ids+(record.memory_id,),state.invalidated_record_ids,seq)
def authorized_entry(entry,scope,host):
    r,_,e=entry
    return r.scope_commitment==scope.scope_commitment and r.owner_agent_id==scope.owner_agent_id and r.source_task_id in scope.allowed_task_ids and r.source_task_id in host.source_task_ids and e.experience_commitment in host.source_commitments

def retrieve(state,scope,query,host,*,stop=False,now=0,deadline=1,budget=4096):
    need(type(state) is MemoryState and type(query) is MemoryQuery);guard(stop,now,deadline,budget,1+state.record_count*(1+len(query.query_terms)));state.__post_init__();query.__post_init__();authorize(scope,query.agent_id,query.task_id,query.authorization_ref,host,'READ');need(query.scope_id==scope.scope_id)
    candidates=[]
    for entry in state.entries:
        r,content,e=entry
        if r.memory_id not in state.active_record_ids or not authorized_entry(entry,scope,host):continue
        if query.record_ids and r.memory_id not in query.record_ids:continue
        if query.source_task_ids and r.source_task_id not in query.source_task_ids:continue
        if query.content_types and r.content_type not in query.content_types:continue
        score=sum(term.casefold() in content.casefold() for term in query.query_terms)
        if query.query_terms and score==0:continue
        candidates.append((-score,r.memory_id,entry))
    chosen=tuple(item[2] for item in sorted(candidates,key=lambda x:(x[0],x[1]))[:query.max_results])
    return make(MemoryRetrievalResult,'result_commitment','retrieval',query_id=query.query_id,record_ids=tuple(e[0].memory_id for e in chosen),record_commitments=tuple(digest('entry',e) for e in chosen),retrieval_status='OK' if chosen else 'EMPTY',query_commitment=digest('query',query),state_commitment=state.state_commitment,authorization_commitment=host.authorization_commitment)
def assemble(state,scope,query,host,result,**controls):
    need(type(result) is MemoryRetrievalResult);result.__post_init__();need(result==retrieve(state,scope,query,host,**controls),'STALE_OR_FORGED_RETRIEVAL')
    byid={e[0].memory_id:e for e in state.entries};context=tuple(byid[k] for k in result.record_ids);need(len(encoded(context))<=query.max_context_size,'CONTEXT_LIMIT')
    c=digest('context',context)
    return ContextAssembly('assembly:'+digest('assembly',(query,result)),query.agent_id,query.task_id,result.record_ids,c,tuple('DIAGNOSTIC' for _ in context),'DIAGNOSTIC_ONLY',context)
def invalidate(state,scope,agent_id,task_id,authorization_ref,host,memory_id,*,stop=False,now=0,deadline=1,budget=1024):
    guard(stop,now,deadline,budget,1+state.record_count);state.__post_init__();ident(memory_id);authorize(scope,agent_id,task_id,authorization_ref,host,'INVALIDATE')
    entry=next((e for e in state.entries if e[0].memory_id==memory_id),None);need(entry is not None and authorized_entry(entry,scope,host),'RECORD_DENIED')
    if memory_id in state.invalidated_record_ids:return state
    return snapshot(state,state.entries,tuple(k for k in state.active_record_ids if k!=memory_id),state.invalidated_record_ids+(memory_id,),state.sequence_number+1)

def ingest_governance(arguments,result):
    """Bind available source artifacts. No execution/retry here, no origin attestation.
    Returns only tasks with accepted raw predecessor results; uncertain tasks omitted.
    Caller must pin resulting experience commitments in host memory authorization.
    """
    need(type(arguments) is tuple and len(arguments)==9);request,policy,tasks,delegations,host,registry,bundles,signals,deadline=arguments
    plan,prepared=gov.prepare(request,policy,tasks,delegations,host,registry,bundles)
    need(type(result) is tuple and len(result)==4);state,trace,verdict,raw=result
    for obj,kind in ((state,gov.GovernanceState),(trace,gov.GovernanceTrace),(verdict,gov.GovernanceVerdict)):need(type(obj) is kind);obj.__post_init__()
    need(state.request_id==trace.request_id==verdict.request_id==request and state.status==verdict.execution_status,'GOVERNANCE_BINDING')
    need(trace.binding_commitment==gov.digest((request,policy,tasks,delegations,host,registry,bundles,signals,deadline,plan,state,verdict)),'GOVERNANCE_COMMITMENT')
    need(type(raw) is tuple and len(raw)<=16);refs(tuple(k for k,_ in raw),16);outcomes={o.task_id:o for o in trace.task_outcomes};experiences=[]
    for k,execution in raw:
        need(k in prepared and k in outcomes);meta,bundle,approved=prepared[k];cost=gov.qualify_output(bundle,approved,execution);s,t,v=execution;o=outcomes[k]
        need(o.execution_status==v.execution_status and o.trace_commitment==t.trace_commitment and o.confirmed_consumption==cost and o.verification_status==v.verification_status,'OUTCOME_BINDING')
        references=tuple(x.observation_id for x in t.observations);refs(references,8)
        experiences.append(make(ExperienceRecord,'experience_commitment','experience',experience_id='experience:'+digest('experience-id',(request,k,trace.trace_commitment)),task_id=k,agent_id=meta.agent_id,execution_status=v.execution_status,observation_refs=references,trace_commitment=t.trace_commitment,verification_status=v.verification_status))
    return tuple(experiences)
