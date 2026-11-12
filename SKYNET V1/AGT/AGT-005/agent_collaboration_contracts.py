"""AGT005 local diagnostic contracts. Host pins are assumptions, not signatures."""
from dataclasses import dataclass, fields
import agent_memory_contracts as m
from agent_contracts import need, ident, integer, hashcheck

def digest(v): return m.digest('AGT005',v)
def refs(v,n=64): m.refs(v,n)
def body(v): return tuple((f.name,getattr(v,f.name)) for f in fields(v) if not f.name.endswith('_commitment'))
def seal(cls,**kw):
    name=next(f.name for f in fields(cls) if f.name.endswith('_commitment'))
    values=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if not f.name.endswith('_commitment'))
    return cls(**kw,**{name:digest(values)})
class Contract:
    def __post_init__(self):
        need(self.schema_version=='agt005-v1','VERSION');m.encoded(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
    def validate(self): pass
    def sealed(self,name): need(getattr(self,name)==digest(body(self)),'COMMITMENT')
@dataclass(frozen=True)
class CollaborationSession(Contract):
    session_id:str;owner_id:str;participant_agent_ids:tuple;authorized_task_ids:tuple;session_budget:int;session_commitment:str;schema_version:str='agt005-v1'
    def validate(self):
        refs(self.participant_agent_ids,8);refs(self.authorized_task_ids,16);need(bool(self.participant_agent_ids));integer(self.session_budget);self.sealed('session_commitment')
@dataclass(frozen=True)
class CollaborationGrant(Contract):
    grant_id:str;issuer_id:str;sender_agent_id:str;recipient_agent_id:str;allowed_task_ids:tuple;allowed_memory_refs:tuple;allowed_operations:tuple;max_messages:int;grant_commitment:str;schema_version:str='agt005-v1'
    def validate(self):
        refs(self.allowed_task_ids,16);refs(self.allowed_memory_refs,8);refs(self.allowed_operations,2);need(set(self.allowed_operations)<= {'TRANSFER','MESSAGE'});integer(self.max_messages);need(self.max_messages<=64);need(self.sender_agent_id!=self.recipient_agent_id and self.issuer_id!=self.sender_agent_id,'SELF_DELEGATION');self.sealed('grant_commitment')
@dataclass(frozen=True)
class AgentMessage(Contract):
    message_id:str;session_id:str;sender_agent_id:str;recipient_agent_id:str;source_task_id:str;sequence_number:int;payload_commitment:str;source_refs:tuple;trust_status:str='DIAGNOSTIC';schema_version:str='agt005-v1'
    def validate(self):
        integer(self.sequence_number);need(self.sequence_number>0);refs(self.source_refs,8);need(bool(self.source_refs));need(self.trust_status=='DIAGNOSTIC','TRUST_PROMOTION')
@dataclass(frozen=True)
class ContextTransfer(Contract):
    transfer_id:str;source_agent_id:str;target_agent_id:str;memory_refs:tuple;source_scope_commitment:str;target_scope_commitment:str;transfer_commitment:str;schema_version:str='agt005-v1'
    def validate(self):
        refs(self.memory_refs,8);need(bool(self.memory_refs));need(self.source_agent_id!=self.target_agent_id)
        need(self.transfer_commitment==digest((self.transfer_id,self.source_agent_id,self.target_agent_id,self.memory_refs,self.source_scope_commitment,self.target_scope_commitment,self.schema_version)),'COMMITMENT')
@dataclass(frozen=True)
class TaskHandoff(Contract):
    handoff_id:str;source_agent_id:str;target_agent_id:str;task_id:str;parent_authorization_ref:str;handoff_status:str;handoff_commitment:str;schema_version:str='agt005-v1'
    def validate(self):
        ident(self.parent_authorization_ref);need(self.handoff_status in ('READY','BLOCKED_DEPENDENCY','FAILED_DEPENDENCY','ALREADY_ASSIGNED','DENIED'));self.sealed('handoff_commitment')
@dataclass(frozen=True)
class CollaborationState(Contract):
    session_id:str;ordered_message_ids:tuple;completed_handoffs:tuple;rejected_operations:tuple;consumed_budget:int;remaining_budget:int;state_commitment:str;history:tuple=();assignments:tuple=();session_pin:str='';schema_version:str='agt005-v1'
    def validate(self):
        refs(self.ordered_message_ids);refs(self.completed_handoffs,16);refs(self.rejected_operations,64);integer(self.consumed_budget);integer(self.remaining_budget);need(self.consumed_budget==len(self.ordered_message_ids)+len(self.completed_handoffs));hashcheck(self.session_pin);need(type(self.history) is tuple and len(self.history)<=80);need(type(self.assignments) is tuple and len(self.assignments)==len(self.completed_handoffs));refs(tuple(a[0] for a in self.assignments),16);need(len(self.history)==self.consumed_budget);self.sealed('state_commitment')
@dataclass(frozen=True)
class CollaborationTrace(Contract):
    trace_id:str;session_id:str;ordered_events:tuple;source_commitments:tuple;trace_commitment:str;schema_version:str='agt005-v1'
    def validate(self):
        need(type(self.ordered_events) is tuple and len(self.ordered_events)<=80);need(type(self.source_commitments) is tuple and len(self.source_commitments)<=64)
        for h in self.source_commitments: hashcheck(h)
        self.sealed('trace_commitment')
@dataclass(frozen=True)
class CollaborationVerdict(Contract):
    session_id:str;execution_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt005-v1'
    def validate(self):
        need(self.execution_status in ('DIAGNOSTIC_DELIVERED','EMPTY'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class HostPolicy:
    """Supplied exclusively by trusted host, never by messages. Pin current snapshots."""
    session_commitment:str;grant_commitments:tuple;memory_state_commitment:str;access_commitments:tuple
    expected_state:str='';handoff_approvals:tuple=()
    def __post_init__(self):
        hashcheck(self.session_commitment);hashcheck(self.memory_state_commitment);hashcheck(self.expected_state)
        for values in (self.grant_commitments,self.access_commitments,self.handoff_approvals):
            need(type(values) is tuple and len(values)<=64 and len(set(values))==len(values))
            for h in values: hashcheck(h)
