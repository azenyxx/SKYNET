"""Bounded synthetic contracts; no authority can be represented."""
from dataclasses import dataclass
from typing import Literal
from cognitive_memory_contracts import DTO,canonical,parse,require,identifier,digest_text,typed,MemoryErrorV1
import hashlib
TransferError=MemoryErrorV1
def digest(kind,value):return hashlib.sha256(('SKYNET:Transfer:'+kind+':v1\0').encode()+canonical(value)).hexdigest()
@dataclass(frozen=True)
class Base(DTO):
 namespace:str
 provenance:tuple[str,...]
 trust:Literal['TEST_ONLY']
 def __post_init__(self):
  super().__post_init__();identifier(self.namespace);require(1<=len(self.provenance)<=8,'PROVENANCE')
  for x in self.provenance:digest_text(x)
 @property
 def commitment(self):return digest(type(self).__name__,self)
 @property
 def executable(self):return False
 @property
 def production_authorized(self):return False
@dataclass(frozen=True)
class DomainEntityV1(DTO):
 entity_id:str;role:Literal['NODE','SUPPLY','DEMAND','STATE'];schema:Literal['entity-v1']='entity-v1'
 def __post_init__(self):super().__post_init__();identifier(self.entity_id)
@dataclass(frozen=True)
class DomainRelationV1(DTO):
 source:str;target:str;relation:Literal['PRECEDES','FLOWS','CAUSES','TRANSITIONS'];schema:Literal['relation-v1']='relation-v1'
 def __post_init__(self):super().__post_init__();identifier(self.source);identifier(self.target);require(self.source!=self.target,'SELF_EDGE')
@dataclass(frozen=True)
class DomainConstraintV1(DTO):
 kind:Literal['DEPENDENCIES','CONSERVATION','CAPACITY','INTERVENTION_REQUIRED','CONFOUNDED','AUTHORIZATION','GUARDS'];schema:Literal['constraint-v1']='constraint-v1'
@dataclass(frozen=True)
class DomainSchemaV1(Base):
 domain_id:str;kind:Literal['DAG','FLOW','CAUSAL','STATE'];entities:tuple[DomainEntityV1,...];relations:tuple[DomainRelationV1,...];constraints:tuple[DomainConstraintV1,...];assumptions:tuple[str,...];schema:Literal['domain-v1']='domain-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.domain_id);require(1<=len(self.entities)<=6 and len(self.relations)<=12,'GRAPH_BOUND');ids={e.entity_id for e in self.entities};require(len(ids)==len(self.entities),'DUPLICATE_ENTITY');require(len(set(self.relations))==len(self.relations),'DUPLICATE_RELATION');require(all(r.source in ids and r.target in ids for r in self.relations),'UNKNOWN_ENTITY');require(len(set(self.constraints))==len(self.constraints),'DUPLICATE_CONSTRAINT');require(1<=len(self.assumptions)<=4,'ASSUMPTIONS')
@dataclass(frozen=True)
class AbstractPatternV1(Base):
 domain_commitment:str;kind:str;roles:tuple[str,...];relations:tuple[DomainRelationV1,...];constraints:tuple[DomainConstraintV1,...];information_loss:tuple[str,...];schema:Literal['pattern-v1']='pattern-v1'
@dataclass(frozen=True)
class ConceptMappingV1(Base):
 source_commitment:str;target_commitment:str;source_ids:tuple[str,...];target_ids:tuple[str,...];schema:Literal['mapping-v1']='mapping-v1'
@dataclass(frozen=True)
class AnalogyCandidateV1(Base):
 mapping:ConceptMappingV1;score:int;ambiguity_count:int;schema:Literal['analogy-v1']='analogy-v1'
@dataclass(frozen=True)
class TransferHypothesisV1(Base):
 mapping:ConceptMappingV1;strategy:Literal['TOPOLOGICAL','CONSERVE','INTERVENTION_ONLY','GUARDED'];assumptions:tuple[str,...];falsification:Literal['TARGET_CONSTRAINT_OR_LABEL_MISMATCH'];epistemic:Literal['HYPOTHESIZED'];schema:Literal['hypothesis-v1']='hypothesis-v1'
@dataclass(frozen=True)
class TransferTaskV1(Base):
 task_id:str;target_commitment:str;values:tuple[int,...];authorized:bool;split:Literal['HELD_OUT'];schema:Literal['task-v1']='task-v1'
 def __post_init__(self):super().__post_init__();identifier(self.task_id);digest_text(self.target_commitment);require(len(self.values)<=8 and all(v<=1000000 for v in self.values),'TASK_BOUND')
@dataclass(frozen=True)
class TransferPredictionV1(Base):
 task_commitment:str;output:tuple[str,...];abstained:bool;epistemic:Literal['HYPOTHESIZED'];schema:Literal['prediction-v1']='prediction-v1'
@dataclass(frozen=True)
class TransferEvidenceV1(Base):
 task:TransferTaskV1;prediction:TransferPredictionV1;expected:tuple[str,...];baseline:tuple[str,...];schema:Literal['transfer-evidence-v1']='transfer-evidence-v1'
@dataclass(frozen=True)
class TransferEvaluationV1(Base):
 evidence:tuple[TransferEvidenceV1,...];total:int;answered:int;correct:int;baseline_correct:int;negative:int;constraints_preserved:int;schema:Literal['evaluation-v1']='evaluation-v1'
@dataclass(frozen=True)
class TransferDecisionV1(Base):
 action:Literal['ABSTRACT','MAP','GENERATE_CANDIDATE','VALIDATE','REVISE_MAPPING','REQUEST_EVIDENCE','ABSTAIN','STOP'];reason:Literal['QUALIFIED_WITHIN_FIXTURE','NEGATIVE_TRANSFER','INSUFFICIENT_EVIDENCE','META_STOP','BUDGET'];schema:Literal['decision-v1']='decision-v1'
@dataclass(frozen=True)
class TransferSessionV1(Base):
 session_id:str;source:DomainSchemaV1;target:DomainSchemaV1;hypothesis:TransferHypothesisV1;evaluation:TransferEvaluationV1;decision:TransferDecisionV1;schema:Literal['session-v1']='session-v1'
 def __post_init__(self):super().__post_init__();identifier(self.session_id);require(len(canonical(self))<=65536,'SESSION_BOUND')
