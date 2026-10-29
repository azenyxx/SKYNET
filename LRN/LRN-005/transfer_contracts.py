"""Immutable offline transfer diagnostics. Hashes are not provenance authority."""
from dataclasses import dataclass, fields
import retention_contracts as r
need,ident,integer,refs,hashcheck=r.need,r.ident,r.integer,r.refs,r.hashcheck
BLOCKERS=r.BLOCKERS+('L04-001','L04-002','L04-003')
COMP=('COMPATIBLE_FOR_EVALUATION','PARTIALLY_COMPATIBLE','INCOMPATIBLE','INSUFFICIENT_EVIDENCE','NOT_QUALIFIED')
STATUS=('CANDIDATE_FOR_CROSS_DOMAIN_VALIDATION','REQUIRES_TARGET_EVIDENCE','NEGATIVE_TRANSFER_RISK','REJECTED','NOT_QUALIFIED')
def digest(v): return r.s.replay.learning.memory.digest('LRN005',v)
def make(cls,**kw):
    body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!='commitment')
    return cls(**kw,commitment=digest((cls.__name__,body)))
def check(v,cls): need(type(v) is cls,'TYPE'); v.__post_init__()
class Contract:
    def __post_init__(self):
        need(self.version=='lrn005-v1','VERSION'); refs(self.provenance)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
        need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
@dataclass(frozen=True)
class SourceDomainProfile(Contract):
    domain_id:str; task_category:str; capabilities:tuple; input_schema:str; output_schema:str; metric_id:str; unit:str; direction:str; constraints:tuple; failures:tuple; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        for x in (self.task_category,self.input_schema,self.output_schema,self.unit): ident(x)
        for x in (self.capabilities,self.constraints,self.failures): refs(x)
        need(self.direction in ('HIGHER','LOWER'),'DIRECTION')
@dataclass(frozen=True)
class TargetDomainProfile(SourceDomainProfile): pass
@dataclass(frozen=True)
class TransferPolicy(Contract):
    policy_id:str; source_id:str; target_id:str; allowed_constraints:tuple; budget:int; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        refs(self.allowed_constraints); integer(self.budget); need(1<=self.budget<=64,'BUDGET')
@dataclass(frozen=True)
class TransferEvidence(Contract):
    request_id:str; source_id:str; target_id:str; adaptation:r.AdaptationEvidence; baseline:r.RetentionBaseline; retention_policy:r.RetentionPolicy; retention:r.RetentionEvaluation; target_measurements:tuple; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        for v,c in ((self.adaptation,r.AdaptationEvidence),(self.baseline,r.RetentionBaseline),(self.retention_policy,r.RetentionPolicy),(self.retention,r.RetentionEvaluation)): check(v,c)
        need(self.retention.input_commitment==r.digest((self.baseline,self.adaptation,self.retention_policy)),'RETENTION_BINDING')
        need(self.retention.evaluation_id==self.adaptation.evaluation_id,'EVALUATION_BINDING')
        need(type(self.target_measurements) is tuple and len(self.target_measurements)<=16,'BOUND')
        for x in self.target_measurements: check(x,r.CapabilitySnapshot)
        refs(tuple(x.snapshot_id for x in self.target_measurements))
@dataclass(frozen=True)
class CompatibilityAssessment(Contract):
    source_id:str; target_id:str; status:str; examined:tuple; covered:tuple; unsupported:tuple; reasons:tuple; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        need(self.status in COMP,'STATUS')
        for x in (self.examined,self.covered,self.unsupported,self.reasons): refs(x)
        need(not set(self.covered)&set(self.unsupported),'COVERAGE')
@dataclass(frozen=True)
class TransferCandidate(Contract):
    request_id:str; source_id:str; target_id:str; status:str; assessment_commitment:str; evidence_commitment:str; reasons:tuple; trust_distribution:tuple; excluded:tuple; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        need(self.status in STATUS,'STATUS'); refs(self.reasons); refs(self.excluded)
        need(type(self.trust_distribution) is tuple and len(self.trust_distribution)<=6,'DISTRIBUTION')
        for pair in self.trust_distribution:
            need(type(pair) is tuple and len(pair)==2,'PAIR'); need(pair[0] in r.s.replay.learning.CLASSES and pair[0]!='VERIFIED_LOCAL','TRUST'); integer(pair[1])
        refs(tuple(x[0] for x in self.trust_distribution))
@dataclass(frozen=True)
class TransferState(Contract):
    processed_ids:tuple; consumed:int; remaining:int; sequence:int; previous_state_commitment:str; policy_commitment:str; history:tuple; provenance:tuple; commitment:str; version:str='lrn005-v1'
    def validate(self):
        refs(self.processed_ids)
        for x in (self.consumed,self.remaining,self.sequence): integer(x)
        need(type(self.history) is tuple and len(self.history)==self.sequence==self.consumed==len(self.processed_ids),'ACCOUNTING')
        for x in self.history: hashcheck(x)
@dataclass(frozen=True)
class TransferVerdict(Contract):
    status:str; blockers:tuple; provenance:tuple; commitment:str; learning_authorized:bool=False; model_update_authorized:bool=False; knowledge_promotion_authorized:bool=False; production_authorized:bool=False; version:str='lrn005-v1'
    def validate(self):
        need(self.status=='NOT_QUALIFIED','GENERALIZATION'); need(self.blockers==BLOCKERS,'BLOCKERS')
        for name in ('learning_authorized','model_update_authorized','knowledge_promotion_authorized','production_authorized'): need(getattr(self,name) is False,'AUTHORITY')
