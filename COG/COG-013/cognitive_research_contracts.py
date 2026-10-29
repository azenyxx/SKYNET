from dataclasses import dataclass,fields,asdict
from functools import lru_cache
from typing import Literal,get_type_hints
from hashlib import sha256
from cognitive_memory_contracts import DTO,canonical,parse,typed,require,identifier,digest_text,MemoryErrorV1
ResearchError=MemoryErrorV1
Status=Literal['SUPPORTED_WITHIN_MODEL','REFUTED_WITHIN_MODEL','INCONCLUSIVE','NOT_IDENTIFIABLE','INVALID_EXPERIMENT']
def commit(domain,obj):return sha256(('SKYNET:Research:'+domain+':v1\0').encode()+canonical(obj)).hexdigest()
@lru_cache(maxsize=32)
def hints(cls):return get_type_hints(cls)
@dataclass(frozen=True)
class Base(DTO):
 namespace:str;session_id:str;timestamp:int;provenance:tuple[str,...];epistemic:Literal['OBSERVED_SYNTHETIC','HYPOTHESIZED','INFERRED','UNKNOWN'];trust:Literal['TEST_ONLY']
 def __post_init__(self):
  for f in fields(self):typed(getattr(self,f.name),hints(type(self))[f.name])
  identifier(self.namespace);identifier(self.session_id);require(1<=len(self.provenance)<=8,'PROVENANCE')
  for x in self.provenance:digest_text(x)
 @property
 def commitment(self):return commit(type(self).__name__,self)
 @property
 def executable(self):return False
 @property
 def production_authorized(self):return False
@dataclass(frozen=True)
class ResearchObservationV1(Base):
 x:int;y:int;origin:Literal['INITIAL','EXPERIMENT'];environment_id:Literal['A','B','C'];schema:Literal['research-observation-v1']='research-observation-v1'
 def __post_init__(self):super().__post_init__();require(self.x<=4 and self.y<=32 and self.epistemic=='OBSERVED_SYNTHETIC','OBSERVATION')
@dataclass(frozen=True)
class ResearchDomainV1(Base):
 environment_id:Literal['A','B','C'];observations:tuple[ResearchObservationV1,...];limitations:tuple[str,...];schema:Literal['research-domain-v1']='research-domain-v1'
@dataclass(frozen=True)
class ResearchGapV1(Base):
 category:Literal['COMPETING_RULES','CONFOUNDED','CONTRADICTORY','UNDEREXPLORED'];severity:int;source_commitment:str;schema:Literal['research-gap-v1']='research-gap-v1'
@dataclass(frozen=True)
class ResearchQuestionV1(Base):
 question_id:str;gap_commitment:str;test:Literal['DISCRIMINATE_RULES','IDENTIFY_CAUSAL_EFFECT','RESOLVE_CONFLICT'];schema:Literal['research-question-v1']='research-question-v1'
@dataclass(frozen=True)
class ResearchHypothesisV1(Base):
 hypothesis_id:str;rule:Literal['LINEAR','QUADRATIC','CONSTANT','CAUSAL','COMMON_CAUSE'];assumptions:tuple[str,...];falsification:Literal['ANY_MISMATCH','INDEPENDENT_INTERVENTION_REQUIRED'];schema:Literal['research-hypothesis-v1']='research-hypothesis-v1'
@dataclass(frozen=True)
class ResearchExperimentV1(Base):
 experiment_id:str;domain_commitment:str;question_commitment:str;operation:Literal['QUERY_FIXED_ENVIRONMENT'];x:int;expected_outputs:tuple[int,...];steps:int;schema:Literal['research-experiment-v1']='research-experiment-v1'
 def __post_init__(self):super().__post_init__();require(self.x<=4 and self.steps==1 and len(self.expected_outputs)<=8,'EXPERIMENT_BOUND')
@dataclass(frozen=True)
class ResearchProtocolV1(Base):
 operation:Literal['QUERY_FIXED_ENVIRONMENT'];seed:int;stop_after:int;schema:Literal['research-protocol-v1']='research-protocol-v1'
@dataclass(frozen=True)
class ResearchEvidenceV1(Base):
 experiment_commitment:str;observation_commitment:str;environment_commitment:str;schema:Literal['research-evidence-v1']='research-evidence-v1'
@dataclass(frozen=True)
class ResearchResultV1(Base):
 hypothesis_commitment:str;status:Status;matches:int;tested:int;evidence_commitments:tuple[str,...];schema:Literal['research-result-v1']='research-result-v1'
@dataclass(frozen=True)
class ResearchFindingV1(Base):
 status:Status;limitations:tuple[str,...];schema:Literal['research-finding-v1']='research-finding-v1'
@dataclass(frozen=True)
class ResearchContradictionV1(Base):
 x:int;values:tuple[int,...];schema:Literal['research-contradiction-v1']='research-contradiction-v1'
@dataclass(frozen=True)
class ResearchDecisionV1(Base):
 action:Literal['INVESTIGATE','DESIGN_EXPERIMENT','RUN_ALLOWED_EXPERIMENT','REVISE_HYPOTHESIS','REQUEST_EVIDENCE','ABSTAIN','STOP'];reason:Literal['COMPETING_RULES','CONFIRMED_WITHIN_MODEL','CONFOUNDED','CONTRADICTORY','META_STOP','META_RESTRICTION','BUDGET','COMPLETE'];schema:Literal['research-decision-v1']='research-decision-v1'
@dataclass(frozen=True)
class ResearchBudgetV1(Base):
 max_iterations:int;max_experiments:int;max_steps:int;timeout_ms:int;retries:int;schema:Literal['research-budget-v1']='research-budget-v1'
 def __post_init__(self):super().__post_init__();require(1<=self.max_iterations<=8 and 0<=self.max_experiments<=8 and 0<=self.max_steps<=64 and 1<=self.timeout_ms<=1000 and self.retries==0,'BUDGET')
@dataclass(frozen=True)
class ResearchSessionV1(Base):
 domain:ResearchDomainV1;budget:ResearchBudgetV1;question:ResearchQuestionV1;hypotheses:tuple[ResearchHypothesisV1,...];experiments:tuple[ResearchExperimentV1,...];observations:tuple[ResearchObservationV1,...];evidence:tuple[ResearchEvidenceV1,...];results:tuple[ResearchResultV1,...];decisions:tuple[ResearchDecisionV1,...];iterations:int;terminal:Literal['STOP','ABSTAIN','REQUEST_EVIDENCE'];schema:Literal['research-session-v1']='research-session-v1'
