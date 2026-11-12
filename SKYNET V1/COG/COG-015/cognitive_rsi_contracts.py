"""Data-only, TEST_ONLY improvement contracts."""
from dataclasses import dataclass
from typing import Literal
import hashlib
from cognitive_memory_contracts import DTO,canonical,parse,require,typed,identifier,digest_text,MemoryErrorV1
RSIError=MemoryErrorV1
def digest(domain,value):return hashlib.sha256(('SKYNET:RSI:'+domain+':v1\0').encode()+canonical(value)).hexdigest()
@dataclass(frozen=True)
class Base(DTO):
 namespace:str;session_id:str;provenance:tuple[str,...];trust:Literal['TEST_ONLY']
 def __post_init__(self):
  super().__post_init__();identifier(self.namespace);identifier(self.session_id);require(1<=len(self.provenance)<=8,'PROVENANCE')
  for h in self.provenance:digest_text(h)
 @property
 def commitment(self):return digest(type(self).__name__,self)
 @property
 def executable(self):return False
 @property
 def production_authorized(self):return False
 @property
 def trusted_verification(self):return False
@dataclass(frozen=True)
class ImprovementMetricV1(DTO):
 outputs:tuple[str,...];expected:tuple[str,...];correct:int;constraints:int;operations:int;failures:int;abstention_correct:int;total:int;schema:Literal['metric-v1']='metric-v1'
 def __post_init__(self):super().__post_init__();require(len(self.outputs)==len(self.expected)==self.total<=16,'METRIC_SIZE');require(self.correct<=self.total and self.constraints<=self.total and self.failures<=self.total,'METRIC_BOUND');require(self.operations<=128,'RESOURCE_BOUND')
@dataclass(frozen=True)
class ImprovementBaselineV1(Base):
 scenario:Literal['RESOURCE','ACCURACY','RESEARCH','TRANSFER'];fixture_commitment:str;component_commitments:tuple[str,...];strategy:Literal['REPEAT','NAME_ONLY'];evaluation_version:Literal['fixed-v1'];seed:int;schema:Literal['baseline-v1']='baseline-v1'
 def __post_init__(self):super().__post_init__();digest_text(self.fixture_commitment);require(self.seed==0,'SEED');require(len(self.component_commitments)<=8,'COMPONENT_LIMIT')
@dataclass(frozen=True)
class ImprovementObservationV1(Base):
 baseline_commitment:str;metrics:ImprovementMetricV1;revoked:bool;epistemic:Literal['OBSERVED_SYNTHETIC'];schema:Literal['observation-v1']='observation-v1'
@dataclass(frozen=True)
class ImprovementBottleneckV1(Base):
 observation_commitment:str;kind:Literal['REDUNDANT_WORK','FALSE_TRANSFER','NO_MEASURED_DEFICIENCY'];severity:Literal['MEDIUM','HIGH','UNKNOWN'];schema:Literal['bottleneck-v1']='bottleneck-v1'
@dataclass(frozen=True)
class ImprovementOpportunityV1(Base):
 bottleneck_commitment:str;category:Literal['CACHE_SELECTION','RESEARCH_SELECTION','CONSTRAINT_FILTER'];schema:Literal['opportunity-v1']='opportunity-v1'
@dataclass(frozen=True)
class ImprovementProposalV1(Base):
 proposal_id:str;baseline_commitment:str;bottleneck:ImprovementBottleneckV1;strategy:Literal['MEMO','FAST','DISCRIMINATE','STRICT'];assumptions:tuple[str,...];rejection:Literal['ANY_REGRESSION'];rollback:Literal['RESTORE_LOCAL_SNAPSHOT'];schema:Literal['proposal-v1']='proposal-v1'
 def __post_init__(self):super().__post_init__();digest_text(self.proposal_id);digest_text(self.baseline_commitment)
@dataclass(frozen=True)
class ImprovementCandidateV1(Base):
 proposal:ImprovementProposalV1;parent_commitment:str;depth:int;operation_limit:int;epistemic:Literal['HYPOTHESIZED'];schema:Literal['candidate-v1']='candidate-v1'
 def __post_init__(self):super().__post_init__();digest_text(self.parent_commitment);require(self.depth<=1 and 1<=self.operation_limit<=128,'CANDIDATE_BOUND')
@dataclass(frozen=True)
class ImprovementExperimentV1(Base):
 baseline_commitment:str;candidate_commitment:str;fixture_commitment:str;schema:Literal['experiment-v1']='experiment-v1'
@dataclass(frozen=True)
class ImprovementEvaluationV1(Base):
 baseline_commitment:str;candidate_commitment:str;baseline_metrics:ImprovementMetricV1;candidate_metrics:ImprovementMetricV1;regressions:int;schema:Literal['evaluation-v1']='evaluation-v1'
@dataclass(frozen=True)
class ImprovementRegressionV1(Base):
 candidate_commitment:str;count:int;schema:Literal['regression-v1']='regression-v1'
@dataclass(frozen=True)
class ImprovementChallengeV1(Base):
 candidate_commitment:str;evaluation_commitment:str;adversarial_correct:int;adversarial_total:int;status:Literal['CONSISTENT','REGRESSION'];schema:Literal['challenge-v1']='challenge-v1'
@dataclass(frozen=True)
class ImprovementDecisionV1(Base):
 candidate_commitment:str;action:Literal['REJECT','ABSTAIN','STOP','RECOMMEND_FOR_HUMAN_REVIEW'];reason:Literal['REGRESSION','NO_GAIN','VERIFIED_SYNTHETIC_GAIN','META_STOP'];schema:Literal['decision-v1']='decision-v1'
@dataclass(frozen=True)
class ImprovementRollbackV1(Base):
 baseline_commitment:str;before_commitment:str;restored_commitment:str;status:Literal['LOCAL_SNAPSHOT_RESTORED'];schema:Literal['rollback-v1']='rollback-v1'
@dataclass(frozen=True)
class ImprovementSessionV1(Base):
 baseline:ImprovementBaselineV1;observation:ImprovementObservationV1;candidate:ImprovementCandidateV1;evaluation:ImprovementEvaluationV1;challenge:ImprovementChallengeV1;decision:ImprovementDecisionV1;rollback:ImprovementRollbackV1;schema:Literal['session-v1']='session-v1'
 def __post_init__(self):super().__post_init__();require(len(canonical(self))<=65536,'SESSION_BOUND')
