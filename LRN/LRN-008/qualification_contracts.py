"""Qualification records are diagnostics, never learning authority."""
from dataclasses import dataclass,fields
import learning_validation as v
need,ident,integer,refs,hashcheck=v.need,v.ident,v.integer,v.refs,v.hashcheck
STAGES=tuple('LRN-%03d'%n for n in range(1,9))
FLAGS=('learning_authorized','model_update_authorized','knowledge_promotion_authorized','production_authorized','strategy_change_authorized','policy_change_authorized')
FINDINGS=tuple(('L%02d-%03d'%(stage,n),'P1' if (stage==1 and n in (1,2)) or (stage==2 and n==2) or (stage>=3 and n==1) else 'P2','LRN-%03d'%stage,'OPEN','OWNER_REPORTED','DESCRIPTION_NOT_REVERIFIED','INDEPENDENT_REMEDIATION_EVIDENCE','NOT_QUALIFIED') for stage in range(1,8) for n in range(1,5 if stage==1 else 4))+(('A09-001','P1','AGT-009','OPEN','OWNER_REPORTED','INHERITED_RUNTIME_FAILURE','INDEPENDENT_REMEDIATION_EVIDENCE','NOT_QUALIFIED'),)
PRIORITIES=('INDEPENDENT_PROVENANCE','ORIGINAL_EXPERIENCES','REAL_BASELINE_AND_CANDIDATE_MEASUREMENTS','DURABLE_REPLAY_AND_ROLLBACK','REGRESSION_AND_NEGATIVE_TRANSFER','ADVERSARIAL_CROSS_STAGE_TESTS','AGT_COG_P1_REMEDIATION')
def digest(x): return v.m.t.r.s.replay.learning.memory.digest('LRN008',x)
def make(cls,**kw):
    body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!='commitment')
    return cls(**kw,commitment=digest((cls.__name__,body)))
def check(x,c): need(type(x) is c,'TYPE'); x.__post_init__()
class Contract:
    def __post_init__(self):
        need(self.version=='lrn008-v1','VERSION'); refs(self.provenance)
        for f in fields(self):
            x=getattr(self,f.name)
            if f.name.endswith('_id'): ident(x)
            if f.name.endswith('_commitment'): hashcheck(x)
        self.validate()
        need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
@dataclass(frozen=True)
class StageQualification(Contract):
    stage_id:str; reported_status:str; artifact_status:str; artifact_commitment:str; test_status:str; reproduction:str; integration:str; synthetic:bool; open_findings:tuple; unqualified:tuple; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self):
        need(self.stage_id in STAGES,'STAGE'); need(self.reported_status in ('CLOSED PARTIAL','UNKNOWN'),'CLOSURE')
        need(self.artifact_status in ('REPORTED','UNAVAILABLE'),'ARTIFACT'); need(self.test_status in ('REPORTED','NOT_QUALIFIED'),'TESTS')
        need(self.reproduction=='NOT_QUALIFIED' and self.integration in ('NOT_QUALIFIED','UNAVAILABLE'),'REPRODUCTION')
        need(type(self.synthetic) is bool,'BOOL'); refs(self.open_findings); refs(self.unqualified)
@dataclass(frozen=True)
class EvidenceInventory(Contract):
    source_commitment:str; missing:tuple; classification:str; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self): refs(self.missing); need(self.classification=='STRUCTURALLY_BOUND_NOT_INDEPENDENT','PROVENANCE')
@dataclass(frozen=True)
class IntegrationCoverage(Contract):
    source_commitment:str; executed:tuple; unqualified:tuple; synthetic:bool; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self): refs(self.executed); refs(self.unqualified); need(self.synthetic is True,'SYNTHETIC')
@dataclass(frozen=True)
class FindingRegister(Contract):
    entries:tuple; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self): need(self.entries==FINDINGS,'FINDING_SUPPRESSION_OR_CLOSURE')
@dataclass(frozen=True)
class SafetyBoundaryAssessment(Contract):
    checked:tuple; not_established:tuple; source_commitment:str; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self): refs(self.checked); refs(self.not_established); need(set(self.checked)<=set(FLAGS),'FLAGS')
@dataclass(frozen=True)
class LearningReadinessAssessment(Contract):
    dimensions:tuple; priorities:tuple; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self):
        need(self.dimensions==('ARCHITECTURE_IMPLEMENTED_PARTIAL','INTEGRATION_PARTIALLY_QUALIFIED','EVIDENCE_NOT_QUALIFIED','LEARNING_EXECUTION_NOT_AUTHORIZED','BLOCKED_BY_CRITICAL_FINDINGS'),'READINESS')
        need(self.priorities==PRIORITIES,'PRIORITIES')
@dataclass(frozen=True)
class QualificationState(Contract):
    processed_ids:tuple; consumed:int; remaining:int; sequence:int; previous_state_commitment:str; history:tuple; provenance:tuple; commitment:str; version:str='lrn008-v1'
    def validate(self):
        refs(self.processed_ids)
        for x in (self.consumed,self.remaining,self.sequence): integer(x)
        need(self.consumed+self.remaining==32 and type(self.history) is tuple and len(self.history)==self.sequence==len(self.processed_ids),'ACCOUNTING')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class QualificationVerdict(Contract):
    status:str; provenance:tuple; commitment:str; learning_authorized:bool=False; model_update_authorized:bool=False; knowledge_promotion_authorized:bool=False; production_authorized:bool=False; strategy_change_authorized:bool=False; policy_change_authorized:bool=False; version:str='lrn008-v1'
    def validate(self):
        need(self.status=='CLOSED PARTIAL','STATUS')
        for flag in FLAGS: need(getattr(self,flag) is False,'AUTHORITY')
