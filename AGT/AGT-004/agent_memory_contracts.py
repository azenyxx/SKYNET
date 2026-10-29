"""Bounded diagnostic memory DTOs. Integrity hashes never confer authority."""
from dataclasses import dataclass,fields,replace
import json,hashlib
import agent_contracts as ac
from agent_contracts import need,ident,integer,hashcheck
TRUST=('DIAGNOSTIC','UNVERIFIED','INVALIDATED','EXTERNALLY_ATTESTED_NOT_QUALIFIED')
OPS=('READ','WRITE','INVALIDATE')
def refs(v,limit=256):
    need(type(v) is tuple and len(v)<=limit)
    for x in v:ident(x)
    need(len(set(v))==len(v),'DUPLICATE')
def encoded(v):return json.dumps(ac.plain(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(domain,v):return hashlib.sha256(('SKYNET:AGT004:'+domain+':v1\0').encode()+encoded(v)).hexdigest()
def payload(v,omit):return tuple((f.name,getattr(v,f.name)) for f in fields(v) if f.name not in omit)
def commitment(v,field,domain):need(getattr(v,field)==digest(domain,payload(v,(field,))),'COMMITMENT')
def make(cls,field,domain,**kw):
    # Construct hash from declared fields without creating an invalid temporary DTO.
    values=[]
    for f in fields(cls):
        if f.name!=field:values.append((f.name,kw[f.name] if f.name in kw else f.default))
    return cls(**kw,**{field:digest(domain,tuple(values))})
class Contract:
    def __post_init__(self):
        need(self.schema_version=='agt004-v1','VERSION');encoded(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'):ident(v)
            if f.name.endswith('_commitment'):hashcheck(v)
        self.validate()
    def validate(self):pass
@dataclass(frozen=True)
class MemoryRecord(Contract):
    memory_id:str;owner_agent_id:str;source_task_id:str;source_observation_id:str;content_commitment:str;content_type:str;trust_status:str;created_sequence:int;scope_commitment:str;source_refs:tuple;schema_version:str='agt004-v1'
    def validate(self):
        need(self.content_type in ('TEXT','EXPERIENCE'));need(self.trust_status in TRUST);integer(self.created_sequence);need(self.created_sequence>0);refs(self.source_refs,8);need(self.source_observation_id in self.source_refs)
@dataclass(frozen=True)
class MemoryScope(Contract):
    scope_id:str;owner_agent_id:str;allowed_agent_ids:tuple;allowed_task_ids:tuple;allowed_operations:tuple;scope_commitment:str;schema_version:str='agt004-v1'
    def validate(self):
        refs(self.allowed_agent_ids,32);refs(self.allowed_task_ids,32);refs(self.allowed_operations,3);need(set(self.allowed_operations)<=set(OPS));commitment(self,'scope_commitment','scope')
@dataclass(frozen=True)
class MemoryWriteRequest(Contract):
    request_id:str;agent_id:str;task_id:str;scope_id:str;content:str;source_refs:tuple;authorization_ref:str;content_type:str='TEXT';schema_version:str='agt004-v1'
    def validate(self):
        ident(self.authorization_ref);need(type(self.content) is str);need(len(encoded(self.content))<=4096,'CONTENT_LIMIT');refs(self.source_refs,8);need(bool(self.source_refs));need(self.content_type in ('TEXT','EXPERIENCE'))
@dataclass(frozen=True)
class MemoryQuery(Contract):
    query_id:str;agent_id:str;task_id:str;scope_id:str;query_terms:tuple;max_results:int;max_context_size:int;authorization_ref:str;record_ids:tuple=();source_task_ids:tuple=();content_types:tuple=();schema_version:str='agt004-v1'
    def validate(self):
        ident(self.authorization_ref);need(type(self.query_terms) is tuple and len(self.query_terms)<=8)
        for t in self.query_terms:need(type(t) is str and 0<len(t)<=64)
        need(len(set(self.query_terms))==len(self.query_terms));integer(self.max_results);integer(self.max_context_size);need(self.max_results<=16 and self.max_context_size<=16384);refs(self.record_ids,16);refs(self.source_task_ids,32);refs(self.content_types,2);need(set(self.content_types)<=set(('TEXT','EXPERIENCE')))
@dataclass(frozen=True)
class MemoryRetrievalResult(Contract):
    query_id:str;record_ids:tuple;record_commitments:tuple;retrieval_status:str;result_commitment:str;query_commitment:str;state_commitment:str;authorization_commitment:str;schema_version:str='agt004-v1'
    def validate(self):
        refs(self.record_ids,16);need(type(self.record_commitments) is tuple and len(self.record_commitments)==len(self.record_ids))
        for h in self.record_commitments:hashcheck(h)
        need(self.retrieval_status in ('OK','EMPTY'));need((self.retrieval_status=='EMPTY')==(len(self.record_ids)==0));commitment(self,'result_commitment','retrieval')
@dataclass(frozen=True)
class ExperienceRecord(Contract):
    experience_id:str;task_id:str;agent_id:str;execution_status:str;observation_refs:tuple;trace_commitment:str;experience_commitment:str;verification_status:str='NOT_ESTABLISHED';assurance:str='LOCAL_DIAGNOSTIC_NOT_QUALIFIED';schema_version:str='agt004-v1'
    def validate(self):
        refs(self.observation_refs,8);need(self.execution_status in ac.TERMINAL);need(self.verification_status=='NOT_ESTABLISHED' and self.assurance=='LOCAL_DIAGNOSTIC_NOT_QUALIFIED');commitment(self,'experience_commitment','experience')
@dataclass(frozen=True)
class MemoryState(Contract):
    store_id:str;record_count:int;active_record_ids:tuple;invalidated_record_ids:tuple;sequence_number:int;state_commitment:str;entries:tuple=();schema_version:str='agt004-v1'
    def validate(self):
        integer(self.record_count);integer(self.sequence_number);refs(self.active_record_ids);refs(self.invalidated_record_ids);refs(self.active_record_ids+self.invalidated_record_ids)
        need(type(self.entries) is tuple and len(self.entries)<=256 and self.record_count==len(self.entries));ids=[]
        for entry in self.entries:
            need(type(entry) is tuple and len(entry)==3);r,content,e=entry;need(type(r) is MemoryRecord and type(e) is ExperienceRecord);r.__post_init__();e.__post_init__();need(type(content) is str and len(encoded(content))<=4096);need(r.content_commitment==digest('content',content));need(r.source_task_id==e.task_id and r.owner_agent_id==e.agent_id and r.source_refs==e.observation_refs,'PROVENANCE');need(r.trust_status=='DIAGNOSTIC');ids.append(r.memory_id)
        refs(tuple(ids));need(set(ids)==set(self.active_record_ids+self.invalidated_record_ids));need(tuple(sorted(self.active_record_ids))==self.active_record_ids and tuple(sorted(self.invalidated_record_ids))==self.invalidated_record_ids);commitment(self,'state_commitment','state')
@dataclass(frozen=True)
class ContextAssembly(Contract):
    assembly_id:str;agent_id:str;task_id:str;memory_refs:tuple;context_commitment:str;trust_summary:tuple;assembly_status:str;context:tuple;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt004-v1'
    def validate(self):
        refs(self.memory_refs,16);need(type(self.context) is tuple and len(self.context)==len(self.memory_refs));need(self.trust_summary==tuple('DIAGNOSTIC' for _ in self.memory_refs));need(self.assembly_status=='DIAGNOSTIC_ONLY');need(self.production_authorized is False and self.knowledge_promotion_authorized is False);need(len(encoded(self.context))<=16384);need(self.context_commitment==digest('context',self.context))
@dataclass(frozen=True)
class HostAccess(Contract):
    """Trusted host input; never deserialize this from agent memory."""
    agent_id:str;task_id:str;authorization_ref:str;scope_commitment:str;allowed_operations:tuple;source_task_ids:tuple;source_commitments:tuple;authorization_commitment:str;schema_version:str='agt004-v1'
    def validate(self):
        ident(self.authorization_ref);refs(self.allowed_operations,3);need(set(self.allowed_operations)<=set(OPS));refs(self.source_task_ids,32);need(type(self.source_commitments) is tuple and len(self.source_commitments)<=32)
        for h in self.source_commitments:hashcheck(h)
        need(len(set(self.source_commitments))==len(self.source_commitments));commitment(self,'authorization_commitment','authorization')
