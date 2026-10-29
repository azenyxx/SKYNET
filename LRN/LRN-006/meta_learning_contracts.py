"""Bounded diagnostic meta-learning contracts; no independent authority."""
from dataclasses import dataclass,fields
import transfer_contracts as t
need,ident,integer,refs,hashcheck=t.need,t.ident,t.integer,t.refs,t.hashcheck
BLOCKERS=t.BLOCKERS+('L05-001','L05-002','L05-003')
STATUSES=('PREFERRED_FOR_VALIDATION','COMPARABLE_NO_WINNER','INSUFFICIENT_EVIDENCE','REGRESSION_RISK','INCOMPATIBLE','NOT_QUALIFIED')
KINDS=('STRATEGY_SELECTION_CHANGE','EVIDENCE_THRESHOLD_CHANGE','EVALUATION_SCHEDULE_CHANGE','REPLAY_ALLOCATION_CHANGE')
def digest(v): return t.r.s.replay.learning.memory.digest('LRN006',v)
def make(cls,**kw):
    body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!='commitment')
    return cls(**kw,commitment=digest((cls.__name__,body)))
def check(v,c): need(type(v) is c,'TYPE'); v.__post_init__()
class Contract:
    def __post_init__(self):
        need(self.version=='lrn006-v1','VERSION'); refs(self.provenance)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
        need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
@dataclass(frozen=True)
class MetaLearningContext(Contract):
    context_id:str; target_id:str; task_category:str; metric_id:str; unit:str; direction:str; population:tuple; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        ident(self.task_category); ident(self.unit); refs(self.population); need(bool(self.population),'POPULATION'); need(self.direction in ('HIGHER','LOWER'),'DIRECTION')
@dataclass(frozen=True)
class StrategyHistory(Contract):
    strategy_id:str; category:str; source:t.SourceDomainProfile; target:t.TargetDomainProfile; evidence:t.TransferEvidence; assessment:t.CompatibilityAssessment; candidate:t.TransferCandidate; verdict:t.TransferVerdict; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        for v,c in ((self.source,t.SourceDomainProfile),(self.target,t.TargetDomainProfile),(self.evidence,t.TransferEvidence),(self.assessment,t.CompatibilityAssessment),(self.candidate,t.TransferCandidate),(self.verdict,t.TransferVerdict)): check(v,c)
        need(self.category in t.r.s.CATEGORIES,'CATEGORY')
        need(self.strategy_id==self.evidence.adaptation.proposal.strategy_id,'STRATEGY_BINDING')
        need(self.candidate.evidence_commitment==self.evidence.commitment and self.candidate.assessment_commitment==self.assessment.commitment,'HISTORY_BINDING')
        need(self.candidate.request_id==self.evidence.request_id,'REQUEST_BINDING')
        for v in (self.evidence,self.assessment,self.candidate): need((v.source_id,v.target_id)==(self.source.domain_id,self.target.domain_id),'DOMAIN_BINDING')
@dataclass(frozen=True)
class MetaLearningPolicy(Contract):
    policy_id:str; existing_policy_commitment:str; budget:int; max_declared_cost:int; proposal_kind:str; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        integer(self.budget); integer(self.max_declared_cost); need(1<=self.budget<=64 and 1<=self.max_declared_cost<=64,'LIMIT'); need(self.proposal_kind in KINDS,'KIND')
@dataclass(frozen=True)
class StrategyPerformanceEvidence(Contract):
    evidence_id:str; history_commitment:str; context_commitment:str; observations:tuple; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        need(type(self.observations) is tuple and len(self.observations)<=8,'BOUND')
        for v in self.observations: check(v,t.r.CapabilitySnapshot)
        refs(tuple(v.snapshot_id for v in self.observations))
@dataclass(frozen=True)
class MetaStrategyAssessment(Contract):
    strategy_id:str; status:str; reasons:tuple; history_commitment:str; performance_commitment:str; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self): need(self.status in STATUSES,'STATUS'); refs(self.reasons)
@dataclass(frozen=True)
class MetaAdaptationProposal(Contract):
    strategy_id:str; existing_policy_commitment:str; adjustment:str; supporting_commitments:tuple; expected_cost:int; uncertainty:str; required_validation:tuple; blockers:tuple; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        need(self.adjustment in KINDS,'ADJUSTMENT'); integer(self.expected_cost)
        refs(self.supporting_commitments)
        for h in self.supporting_commitments: hashcheck(h)
        need(self.uncertainty=='DIAGNOSTIC_NOT_INDEPENDENT','UNCERTAINTY')
        need(self.required_validation==('INDEPENDENT_PROVENANCE','TARGET_VALIDATION','NO_THRESHOLD_RELAXATION','SEPARATE_AUTHORIZATION'),'VALIDATION')
        need(self.blockers==BLOCKERS,'BLOCKERS')
@dataclass(frozen=True)
class MetaLearningState(Contract):
    processed_ids:tuple; consumed:int; remaining:int; sequence:int; previous_state_commitment:str; policy_commitment:str; history:tuple; provenance:tuple; commitment:str; version:str='lrn006-v1'
    def validate(self):
        refs(self.processed_ids)
        for v in (self.consumed,self.remaining,self.sequence): integer(v)
        need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.processed_ids) and self.consumed>=self.sequence,'HISTORY')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class MetaLearningVerdict(Contract):
    status:str; provenance:tuple; commitment:str; learning_authorized:bool=False; model_update_authorized:bool=False; knowledge_promotion_authorized:bool=False; production_authorized:bool=False; strategy_change_authorized:bool=False; policy_change_authorized:bool=False; version:str='lrn006-v1'
    def validate(self):
        need(self.status=='ADVISORY_NOT_QUALIFIED','STATUS')
        for f in fields(self):
            if f.name.endswith('_authorized'): need(getattr(self,f.name) is False,'AUTHORITY')
