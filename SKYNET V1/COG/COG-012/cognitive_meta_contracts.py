from dataclasses import dataclass,fields,asdict
from functools import lru_cache
from typing import Literal,get_type_hints
from hashlib import sha256
from cognitive_memory_contracts import DTO,canonical,parse,typed,require,identifier,digest_text,MemoryErrorV1
MetaContractError=MemoryErrorV1
Codes=Literal['INVALID_SCHEMA','MISSING_EVIDENCE','EVIDENCE_REVOKED','CONTRADICTION','STALE_CONTEXT','UNSUPPORTED_CAUSAL_CLAIM','VALIDATOR_REJECTION','RESOURCE_EXHAUSTION','RETRY_LIMIT','INCOMPLETE_TRACE','UNAUTHORIZED_ACTION','CONFIDENCE_MISREPRESENTATION','INTEGRITY_FAILURE','CROSS_NAMESPACE_ACCESS']
Action=Literal['CONTINUE','RECONSIDER','REQUEST_EVIDENCE','ABSTAIN','STOP']
def commit(domain,obj):return sha256(('SKYNET:Meta:'+domain+':v1\0').encode()+canonical(obj)).hexdigest()
@lru_cache(maxsize=32)
def hints(cls):return get_type_hints(cls)
@dataclass(frozen=True)
class Base(DTO):
 namespace:str;trace_id:str;timestamp:int;source:Literal['RUNTIME','PLANNER','MEMORY','WORLD','CAUSAL','MONITOR','AUDIT'];evidence:tuple[str,...];epistemic:Literal['OBSERVED','INFERRED','UNKNOWN'];trust:Literal['UNVERIFIED']
 def __post_init__(self):
  for f in fields(self):typed(getattr(self,f.name),hints(type(self))[f.name])
  identifier(self.namespace);identifier(self.trace_id);require(len(self.evidence)<=8,'EVIDENCE_LIMIT')
  for e in self.evidence:digest_text(e)
 @property
 def commitment(self):return commit(type(self).__name__,self)
@dataclass(frozen=True)
class MetaEventV1(Base):
 event_id:str;sequence:int;kind:Literal['PLAN_START','MEMORY','WORLD','CAUSAL','PLAN_RESULT','END','RESOURCE','ERROR'];outcome:Literal['OK','REJECTED','MISSING','REVOKED','STALE','CONFLICT','NOT_IDENTIFIABLE','HYPOTHETICAL','UNAUTHORIZED','UNSUPPORTED_CONFIDENCE','FACT_CLAIM','CORRELATION_CAUSAL','UNKNOWN'];input_commitment:str;output_commitment:str;usage:tuple[int,...];schema:Literal['meta-event-v1']='meta-event-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.event_id);digest_text(self.input_commitment);digest_text(self.output_commitment);require(len(self.usage)==5,'RESOURCE_DIMENSIONS');require(len(canonical(self))<=4096,'EVENT_SIZE')
@dataclass(frozen=True)
class MetaTraceV1(Base):
 events:tuple[MetaEventV1,...];schema:Literal['meta-trace-v1']='meta-trace-v1'
@dataclass(frozen=True)
class MetaObservationV1(Base):
 code:Codes;artifact_commitment:str;schema:Literal['meta-observation-v1']='meta-observation-v1'
@dataclass(frozen=True)
class MetaErrorV1(Base):
 code:Codes;severity:Literal['ERROR','WARNING'];schema:Literal['meta-error-v1']='meta-error-v1'
@dataclass(frozen=True)
class MetaAnomalyV1(Base):
 code:Codes;severity:Literal['ERROR','WARNING'];event_commitment:str;recommendation:Action;schema:Literal['meta-anomaly-v1']='meta-anomaly-v1'
@dataclass(frozen=True)
class MetaUncertaintyV1(Base):
 classification:Literal['UNKNOWN','MODEL_RELATIVE','CONTRADICTED'];causes:tuple[str,...];schema:Literal['meta-uncertainty-v1']='meta-uncertainty-v1'
@dataclass(frozen=True)
class MetaConfidenceAssessmentV1(Base):
 total:int;covered:int;brier_numerator:int;brier_denominator:int;ece_numerator:int;ece_denominator:int;calibration_status:Literal['SYNTHETIC_FIXTURE_ONLY'];schema:Literal['meta-confidence-v1']='meta-confidence-v1'
@dataclass(frozen=True)
class MetaContradictionV1(Base):
 artifact_commitments:tuple[str,...];schema:Literal['meta-contradiction-v1']='meta-contradiction-v1'
@dataclass(frozen=True)
class MetaBudgetV1(Base):
 limits:tuple[int,...];retries_used:int;retry_limit:int;schema:Literal['meta-budget-v1']='meta-budget-v1'
 def __post_init__(self):super().__post_init__();require(len(self.limits)==5 and self.retry_limit<=3,'BUDGET')
@dataclass(frozen=True)
class MetaStrategyAssessmentV1(Base):
 recommendation:Action;reason_codes:tuple[str,...];schema:Literal['meta-strategy-v1']='meta-strategy-v1'
@dataclass(frozen=True)
class MetaDecisionV1(Base):
 action:Action;reason_codes:tuple[str,...];trace_commitment:str;budget_commitment:str;policy_version:Literal['meta-policy-v1'];schema:Literal['meta-decision-v1']='meta-decision-v1'
 @property
 def executable(self):return False
 @property
 def production_authorized(self):return False
 @property
 def trusted_verification(self):return False
@dataclass(frozen=True)
class MetaAuditRecordV1(Base):
 sequence:int;trace:MetaTraceV1;budget:MetaBudgetV1;decision:MetaDecisionV1;previous_commitment:str;schema:Literal['meta-audit-v1']='meta-audit-v1'
