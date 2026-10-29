"""Bounded diagnostic recovery DTOs. Host pins are not cryptographic provenance."""
from dataclasses import dataclass,fields
import agent_feedback as feedback
from agent_contracts import need,ident,integer,hashcheck
OPS=('CONTINUE_READY','PAUSE_WORKFLOW','REQUEST_REASSIGNMENT','REQUEST_REPLAN','ESCALATE_TO_HOST','TERMINATE_WORKFLOW')
REASONS=('TASK_FAILED','DEPENDENCY_BLOCKED','AGENT_UNAVAILABLE','RESOURCE_PRESSURE','EXECUTION_UNCERTAIN','STOP_REQUESTED','DEADLINE_REACHED')
def digest(v):return feedback.planning.mc.digest('AGT008',v)
def refs(v,n=16):feedback.refs(v,n)
def ops(v):refs(v,6);need(bool(v) and set(v)<=set(OPS),'OPERATION')
def make(cls,**kw):return cls(**kw,**{cls.HASH:digest(tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!=cls.HASH))})
class Contract:
    HASH=''
    def __post_init__(self):
        need(self.schema_version=='agt008-v1','VERSION');feedback.planning.mc.encoded(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'):ident(v)
            if f.name.endswith('_commitment'):hashcheck(v)
        self.validate()
        if self.HASH:need(getattr(self,self.HASH)==digest(tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=self.HASH)),'COMMITMENT')
    def validate(self):pass
@dataclass(frozen=True)
class RecoveryRequest(Contract):
    HASH='request_commitment'
    request_id:str;goal_id:str;plan_commitment:str;source_state_commitment:str;reason_code:str;requested_operations:tuple;request_commitment:str;schema_version:str='agt008-v1'
    def validate(self):need(self.reason_code in REASONS);ops(self.requested_operations)
@dataclass(frozen=True)
class RecoveryPolicy(Contract):
    HASH='policy_commitment'
    policy_id:str;allowed_operations:tuple;max_attempts:int;resource_ceiling:int;policy_commitment:str;schema_version:str='agt008-v1'
    def validate(self):ops(self.allowed_operations);integer(self.max_attempts);need(1<=self.max_attempts<=4);integer(self.resource_ceiling)
@dataclass(frozen=True)
class AgentAssignment(Contract):
    HASH='assignment_commitment'
    assignment_id:str;task_id:str;source_agent_id:str;target_agent_id:str;required_capabilities:tuple;authorization_commitment:str;assignment_commitment:str;schema_version:str='agt008-v1'
    def validate(self):refs(self.required_capabilities,4);need(set(self.required_capabilities)<=set(feedback.planning.gov.ac.OPS))
@dataclass(frozen=True)
class RecoveryCandidate(Contract):
    HASH='candidate_commitment'
    candidate_id:str;request_id:str;affected_task_ids:tuple;proposed_operations:tuple;estimated_cost:int;candidate_commitment:str;schema_version:str='agt008-v1'
    def validate(self):refs(self.affected_task_ids);need(bool(self.affected_task_ids));ops(self.proposed_operations);integer(self.estimated_cost);need(self.estimated_cost==1,'FIXED_COORDINATION_COST')
@dataclass(frozen=True)
class RecoveryEvaluation(Contract):
    HASH='evaluation_commitment'
    evaluation_id:str;candidate_id:str;feasibility_status:str;constraint_violations:tuple;resource_projection:int;evaluation_commitment:str;schema_version:str='agt008-v1'
    def validate(self):need(self.feasibility_status in ('ELIGIBLE','REQUIRES_HOST_APPROVAL','BLOCKED','NOT_QUALIFIED'));refs(self.constraint_violations);integer(self.resource_projection)
@dataclass(frozen=True)
class RecoveryAuthorization(Contract):
    HASH='authorization_commitment'
    authorization_id:str;candidate_commitment:str;approved_operations:tuple;approved_budget:int;authorization_commitment:str;schema_version:str='agt008-v1'
    def validate(self):ops(self.approved_operations);integer(self.approved_budget)
@dataclass(frozen=True)
class RecoveryState(Contract):
    HASH='state_commitment'
    goal_id:str;active_plan_commitment:str;processed_request_ids:tuple;completed_recovery_ids:tuple;blocked_recovery_ids:tuple;consumed_budget:int;uncertain_consumption:int;remaining_budget:int;state_commitment:str;reserved_capacity:int=0;sequence:int=0;history:tuple=();source_pin:str='0'*64;schema_version:str='agt008-v1'
    def validate(self):
        refs(self.processed_request_ids,4);refs(self.completed_recovery_ids+self.blocked_recovery_ids,4)
        for v in (self.consumed_budget,self.uncertain_consumption,self.remaining_budget,self.reserved_capacity,self.sequence):integer(v)
        hashcheck(self.source_pin);need(self.sequence==len(self.processed_request_ids)==len(self.completed_recovery_ids)+len(self.blocked_recovery_ids));need(type(self.history) is tuple and len(self.history)==self.sequence)
@dataclass(frozen=True)
class RecoveryVerdict(Contract):
    goal_id:str;execution_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt008-v1'
    def validate(self):need(self.execution_status in ('COORDINATION_RECORDED','NOT_QUALIFIED'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class HostPins:
    policy_commitment:str;source_commitment:str;expected_state:str;authorization_commitments:tuple
    def __post_init__(self):
        for v in (self.policy_commitment,self.source_commitment,self.expected_state):hashcheck(v)
        need(type(self.authorization_commitments) is tuple and len(self.authorization_commitments)<=4)
        for v in self.authorization_commitments:hashcheck(v)
