"""Fail-closed validation DTOs; no independent verification authority."""
from dataclasses import dataclass,fields
import meta_learning as m
need,ident,integer,refs,hashcheck=m.need,m.ident,m.integer,m.refs,m.hashcheck
BLOCKERS=m.BLOCKERS+('L06-001','L06-002','L06-003')
STATUSES=('QUALIFIED_FOR_FURTHER_VALIDATION','REQUIRES_INDEPENDENT_EVIDENCE','REGRESSION_BLOCKED','POLICY_BLOCKED','INTEGRATION_NOT_QUALIFIED','REJECTED')
def digest(v): return m.t.r.s.replay.learning.memory.digest('LRN007',v)
def make(cls,**kw):
    body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!='commitment')
    return cls(**kw,commitment=digest((cls.__name__,body)))
def check(v,c): need(type(v) is c,'TYPE'); v.__post_init__()
class Contract:
    def __post_init__(self):
        need(self.version=='lrn007-v1','VERSION'); refs(self.provenance)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
        need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
@dataclass(frozen=True)
class EvidenceChain(Contract):
    request_id:str; context:m.MetaLearningContext; entries:tuple; policy:m.MetaLearningPolicy; previous:m.MetaLearningState; result:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        for v,c in ((self.context,m.MetaLearningContext),(self.policy,m.MetaLearningPolicy),(self.previous,m.MetaLearningState)): check(v,c)
        need(type(self.entries) is tuple and 2<=len(self.entries)<=8,'ENTRIES')
        for pair in self.entries:
            need(type(pair) is tuple and len(pair)==2,'PAIR'); check(pair[0],m.StrategyHistory); check(pair[1],m.StrategyPerformanceEvidence)
        refs(tuple(x[0].strategy_id for x in self.entries))
        need(type(self.result) is tuple and len(self.result)==4,'RESULT')
        check(self.result[0],m.MetaLearningState); check(self.result[3],m.MetaLearningVerdict)
        for collection,cls in ((self.result[1],m.MetaStrategyAssessment),(self.result[2],m.MetaAdaptationProposal)):
            need(type(collection) is tuple and len(collection)<=8,'BOUND')
            for x in collection: check(x,cls)
@dataclass(frozen=True)
class ValidationCandidate(Contract):
    candidate_id:str; strategy_id:str; chain_commitment:str; proposal:m.MetaAdaptationProposal; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self): check(self.proposal,m.MetaAdaptationProposal); need(self.strategy_id==self.proposal.strategy_id,'STRATEGY')
@dataclass(frozen=True)
class ValidationPolicy(Contract):
    policy_id:str; budget:int; max_cost:int; allowed_adjustments:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        integer(self.budget); integer(self.max_cost); need(1<=self.budget<=64 and 1<=self.max_cost<=64,'LIMIT'); refs(self.allowed_adjustments); need(set(self.allowed_adjustments)<=set(m.KINDS),'ADJUSTMENT')
@dataclass(frozen=True)
class ProvenanceAssessment(Contract):
    source_commitment:str; classification:str; qualification:str; missing:tuple; original_classes:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        need(self.classification in ('STRUCTURALLY_BOUND','HOST_ATTESTED','REPORTED_ONLY','CONTRADICTED','UNAVAILABLE'),'NO_INDEPENDENT_AUTHORITY')
        need(self.qualification=='NOT_QUALIFIED','QUALIFICATION'); refs(self.missing)
        need(type(self.original_classes) is tuple and len(self.original_classes)<=32,'BOUND')
        need(all(x in m.t.r.s.replay.learning.CLASSES and x!='VERIFIED_LOCAL' for x in self.original_classes),'TRUST')
@dataclass(frozen=True)
class RegressionGate(Contract):
    baseline_commitment:str; retention_commitment:str; status:str; reasons:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        need(self.status in ('REGRESSION_GATE_PASSED','REGRESSION_DETECTED','INSUFFICIENT_MEASUREMENTS','BASELINE_UNQUALIFIED','NOT_QUALIFIED'),'STATUS'); refs(self.reasons)
@dataclass(frozen=True)
class ValidationAssessment(Contract):
    candidate_id:str; chain_commitment:str; provenance_assessment:ProvenanceAssessment; regression:RegressionGate; status:str; reasons:tuple; blockers:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        check(self.provenance_assessment,ProvenanceAssessment); check(self.regression,RegressionGate); need(self.status in STATUSES and self.status!='QUALIFIED_FOR_FURTHER_VALIDATION','NO_QUALIFIED_AUTHORITY'); refs(self.reasons); need(self.blockers==BLOCKERS,'BLOCKERS')
@dataclass(frozen=True)
class ValidationState(Contract):
    processed_ids:tuple; consumed:int; remaining:int; sequence:int; previous_state_commitment:str; policy_commitment:str; history:tuple; provenance:tuple; commitment:str; version:str='lrn007-v1'
    def validate(self):
        refs(self.processed_ids)
        for v in (self.consumed,self.remaining,self.sequence): integer(v)
        need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.processed_ids) and self.consumed>=self.sequence,'ACCOUNTING')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class ValidationVerdict(Contract):
    status:str; provenance:tuple; commitment:str; learning_authorized:bool=False; model_update_authorized:bool=False; knowledge_promotion_authorized:bool=False; production_authorized:bool=False; strategy_change_authorized:bool=False; policy_change_authorized:bool=False; version:str='lrn007-v1'
    def validate(self):
        need(self.status in STATUSES and self.status!='QUALIFIED_FOR_FURTHER_VALIDATION','NO_INDEPENDENT_AUTHORITY')
        for f in fields(self):
            if f.name.endswith('_authorized'): need(getattr(self,f.name) is False,'AUTHORITY')
