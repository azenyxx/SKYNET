"""Local diagnostic contracts; commitments do not authenticate observations."""
from dataclasses import dataclass, fields
import learning_strategy_contracts as s
from learning_contracts import need, ident, integer, refs, hashcheck

STATUSES=('RETENTION_PRESERVED','REGRESSION_DETECTED','INSUFFICIENT_EVIDENCE','BASELINE_UNQUALIFIED','NOT_QUALIFIED')
BLOCKERS=s.BLOCKERS+('L03-001','L03-002','L03-003')
def digest(v): return s.replay.learning.memory.digest('LRN004',v)
def make(cls,**kw):
    body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!='commitment')
    return cls(**kw,commitment=digest((cls.__name__,body)))
def obj(v,cls):
    need(type(v) is cls,'TYPE'); v.__post_init__()
class Contract:
    def __post_init__(self):
        need(self.version=='lrn004-v1','VERSION')
        refs(self.provenance)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
        need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
@dataclass(frozen=True)
class CapabilitySnapshot(Contract):
    snapshot_id:str; metric_id:str; unit:str; direction:str; population:tuple; value:int; uncertainty:int; quality:str; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        ident(self.unit); refs(self.population); need(bool(self.population),'POPULATION')
        integer(self.value); integer(self.uncertainty)
        need(self.direction in ('HIGHER','LOWER'),'DIRECTION')
        need(self.quality in ('DIAGNOSTIC','UNVERIFIED'),'QUALITY')
@dataclass(frozen=True)
class RetentionBaseline(Contract):
    baseline_id:str; snapshots:tuple; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        need(type(self.snapshots) is tuple and len(self.snapshots)<=16,'BOUND')
        for x in self.snapshots: obj(x,CapabilitySnapshot)
        refs(tuple(x.metric_id for x in self.snapshots)); refs(tuple(x.snapshot_id for x in self.snapshots))
@dataclass(frozen=True)
class RetentionPolicy(Contract):
    policy_id:str; tolerance:int; budget:int; max_cost:int; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        for x in (self.tolerance,self.budget,self.max_cost): integer(x)
        need(1<=self.budget<=64 and 1<=self.max_cost<=64,'BUDGET')
@dataclass(frozen=True)
class AdaptationEvidence(Contract):
    evaluation_id:str; proposal:s.AdaptationProposal; source:s.StrategyEvidence; snapshots:tuple; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        obj(self.proposal,s.AdaptationProposal); obj(self.source,s.StrategyEvidence)
        need(self.proposal.supporting_evidence==(self.source.evidence_id,),'SOURCE_BINDING')
        need(type(self.snapshots) is tuple and len(self.snapshots)<=16,'BOUND')
        for x in self.snapshots: obj(x,CapabilitySnapshot)
        refs(tuple(x.metric_id for x in self.snapshots)); refs(tuple(x.snapshot_id for x in self.snapshots))
@dataclass(frozen=True)
class RegressionAssessment(Contract):
    metric_id:str; status:str; reasons:tuple; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self): need(self.status in STATUSES,'STATUS'); refs(self.reasons)
@dataclass(frozen=True)
class RetentionEvaluation(Contract):
    evaluation_id:str; input_commitment:str; assessments:tuple; status:str; source_diversity:int; estimated_cost:int; blockers:tuple; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        need(self.status in STATUSES,'STATUS'); integer(self.source_diversity); integer(self.estimated_cost)
        need(self.blockers==BLOCKERS,'BLOCKERS')
        need(type(self.assessments) is tuple and len(self.assessments)<=16,'BOUND')
        for x in self.assessments: obj(x,RegressionAssessment)
        refs(tuple(x.metric_id for x in self.assessments))
@dataclass(frozen=True)
class RetentionState(Contract):
    processed_ids:tuple; consumed:int; remaining:int; sequence:int; previous_state_commitment:str; policy_commitment:str; history:tuple; provenance:tuple; commitment:str; version:str='lrn004-v1'
    def validate(self):
        refs(self.processed_ids)
        for x in (self.consumed,self.remaining,self.sequence): integer(x)
        need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.processed_ids),'HISTORY')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class RetentionVerdict(Contract):
    status:str; provenance:tuple; commitment:str; learning_authorized:bool=False; model_update_authorized:bool=False; knowledge_promotion_authorized:bool=False; production_authorized:bool=False; version:str='lrn004-v1'
    def validate(self):
        need(self.status in STATUSES,'STATUS')
        for name in ('learning_authorized','model_update_authorized','knowledge_promotion_authorized','production_authorized'): need(getattr(self,name) is False,'AUTHORITY')
