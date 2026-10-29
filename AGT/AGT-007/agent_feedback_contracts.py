"""Diagnostic feedback contracts; hashes establish integrity, not authority."""
from dataclasses import dataclass,fields
import agent_planning as planning
from agent_contracts import need,ident,integer,hashcheck

def digest(v):return planning.mc.digest('AGT007',v)
def refs(v,n=64):planning.mc.refs(v,n)
def make(cls,**kw):
    values=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!=cls.HASH)
    return cls(**kw,**{cls.HASH:digest(values)})
class Contract:
    HASH=''
    def __post_init__(self):
        need(self.schema_version=='agt007-v1','VERSION');planning.mc.encoded(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'):ident(v)
            if f.name.endswith('_commitment'):hashcheck(v)
        self.validate()
        if self.HASH:need(getattr(self,self.HASH)==digest(tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=self.HASH)),'COMMITMENT')
    def validate(self):pass
@dataclass(frozen=True)
class ObservationRecord(Contract):
    HASH='observation_commitment'
    observation_id:str;goal_id:str;task_id:str;source_component:str;source_commitment:str;execution_status:str;verification_status:str;observed_sequence:int;observation_commitment:str;schema_version:str='agt007-v1'
    def validate(self):
        need(self.source_component=='AGT003_VIA_AGT006');need(self.execution_status in ('COMPLETED','FAILED','BLOCKED','UNCERTAIN','STOPPED','DEADLINE','BUDGET_EXHAUSTED'));need(self.verification_status=='NOT_ESTABLISHED');integer(self.observed_sequence);need(self.observed_sequence>0)
@dataclass(frozen=True)
class FeedbackSignal(Contract):
    HASH='signal_commitment'
    signal_id:str;observation_refs:tuple;signal_type:str;severity:str;confidence_status:str;signal_commitment:str;schema_version:str='agt007-v1'
    def validate(self):
        refs(self.observation_refs,8);need(bool(self.observation_refs));need(self.signal_type in ('TASK_COMPLETED','TASK_FAILED','DEPENDENCY_BLOCKED','RESOURCE_PRESSURE','EXECUTION_UNCERTAIN','PLAN_DEVIATION','STOP_REQUESTED','DEADLINE_REACHED'));need(self.severity in ('INFO','WARNING','CRITICAL'));need(self.confidence_status=='NOT_ESTABLISHED')
@dataclass(frozen=True)
class ProgressSnapshot(Contract):
    HASH='snapshot_commitment'
    snapshot_id:str;goal_id:str;completed_task_ids:tuple;failed_task_ids:tuple;blocked_task_ids:tuple;uncertain_task_ids:tuple;consumed_budget:int;remaining_budget:int;snapshot_commitment:str;uncertain_consumption:int=0;schema_version:str='agt007-v1'
    def validate(self):
        refs(self.completed_task_ids+self.failed_task_ids+self.blocked_task_ids+self.uncertain_task_ids,16)
        for v in (self.consumed_budget,self.remaining_budget,self.uncertain_consumption):integer(v)
@dataclass(frozen=True)
class DeviationAssessment(Contract):
    HASH='assessment_commitment'
    assessment_id:str;goal_id:str;plan_commitment:str;expected_outcomes:tuple;observed_outcomes:tuple;deviation_codes:tuple;assessment_commitment:str;observation_refs:tuple=();schema_version:str='agt007-v1'
    def validate(self):
        refs(self.observation_refs,16);refs(self.deviation_codes,16)
        for group in (self.expected_outcomes,self.observed_outcomes):
            need(type(group) is tuple and len(group)<=16)
            for k,v in group:ident(k);ident(v)
@dataclass(frozen=True)
class CorrectiveProposal(Contract):
    HASH='proposal_commitment'
    proposal_id:str;goal_id:str;proposal_type:str;affected_task_ids:tuple;required_authorization:str;estimated_cost:int;proposal_commitment:str;observation_refs:tuple=();reason_code:str='HOST_REVIEW';schema_version:str='agt007-v1'
    def validate(self):
        refs(self.affected_task_ids,16);refs(self.observation_refs,16);need(bool(self.observation_refs));need(self.proposal_type in ('CONTINUE_AUTHORIZED','PAUSE','ESCALATE_TO_HOST','REQUEST_REPLAN','REQUEST_REASSIGNMENT','TERMINATE_GOAL'));need(self.required_authorization=='TRUSTED_HOST_APPROVAL');integer(self.estimated_cost);need(self.reason_code=='HOST_REVIEW')
@dataclass(frozen=True)
class DecisionPolicy(Contract):
    HASH='policy_commitment'
    policy_id:str;allowed_decisions:tuple;max_proposals:int;resource_ceiling:int;policy_commitment:str;schema_version:str='agt007-v1'
    def validate(self):
        refs(self.allowed_decisions,5);need(set(self.allowed_decisions)<=set(('CONTINUE','PAUSE','ESCALATE','TERMINATE','NO_ACTION')));integer(self.max_proposals);need(self.max_proposals<=8);integer(self.resource_ceiling)
@dataclass(frozen=True)
class FeedbackState(Contract):
    HASH='state_commitment'
    goal_id:str;processed_observation_ids:tuple;accepted_signal_ids:tuple;proposal_ids:tuple;consumed_budget:int;remaining_budget:int;state_commitment:str;history:tuple=();revision:int=0;schema_version:str='agt007-v1'
    def validate(self):
        refs(self.processed_observation_ids,64);refs(self.accepted_signal_ids,32);refs(self.proposal_ids,8);integer(self.consumed_budget);integer(self.remaining_budget);integer(self.revision);need(self.revision<=4);need(type(self.history) is tuple and len(self.history)==self.revision);need(self.consumed_budget==len(self.processed_observation_ids))
@dataclass(frozen=True)
class FeedbackVerdict(Contract):
    goal_id:str;decision_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt007-v1'
    def validate(self):need(self.decision_status in ('CONTINUE','PAUSE','ESCALATE','TERMINATE','NO_ACTION'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class HostPins:
    """Must be supplied by trusted host, never by agent-produced data."""
    goal_commitment:str;policy_commitment:str;expected_state:str;approved_sources:tuple
    def __post_init__(self):
        for h in (self.goal_commitment,self.policy_commitment,self.expected_state):hashcheck(h)
        need(type(self.approved_sources) is tuple and len(self.approved_sources)<=4)
        for h in self.approved_sources:hashcheck(h)
