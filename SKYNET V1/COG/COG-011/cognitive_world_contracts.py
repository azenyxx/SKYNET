"""Strict V1 world DTOs reuse immutable canonical mechanics, not memory authority."""
from dataclasses import dataclass,asdict,fields
from functools import lru_cache
from typing import get_type_hints
from typing import Literal
from hashlib import sha256
from cognitive_memory_contracts import DTO,canonical,parse,require,identifier,digest_text,typed,MemoryErrorV1
WorldError=MemoryErrorV1
Status=Literal['OBSERVED','INFERRED','HYPOTHESIZED','CONTRADICTED','REVOKED','UNKNOWN']
def commit(domain,obj):return sha256(('SKYNET:World:'+domain+':v1\0').encode()+canonical(obj)).hexdigest()
@lru_cache(maxsize=64)
def annotations(cls):return get_type_hints(cls)
@dataclass(frozen=True)
class WorldDTO(DTO):
 namespace:str;provenance:tuple[str,...];epistemic:Status;trust:Literal['UNVERIFIED','PROVISIONAL']
 def __post_init__(self):
  for f in fields(self):typed(getattr(self,f.name),annotations(type(self))[f.name])
  identifier(self.namespace);require(1<=len(self.provenance)<=8,'PROVENANCE')
  for name in ('entity_id','entity_type','subject','predicate','source','relation','evidence_id','model_version'):
   if hasattr(self,name):identifier(getattr(self,name))
  for name in ('state_commitment','previous_commitment','event_commitment'):
   if hasattr(self,name):digest_text(getattr(self,name))
  for p in self.provenance:digest_text(p)
 @property
 def commitment(self):return commit(type(self).__name__,self)
@dataclass(frozen=True)
class WorldEntityV1(WorldDTO):
 entity_id:str;entity_type:str;schema:Literal['entity-v1']='entity-v1'
 def __post_init__(self):super().__post_init__();identifier(self.entity_id);identifier(self.entity_type)
@dataclass(frozen=True)
class WorldEvidenceRefV1(WorldDTO):
 evidence_id:str;content_commitment:str;revoked:bool;schema:Literal['evidence-v1']='evidence-v1'
 def __post_init__(self):super().__post_init__();identifier(self.evidence_id);digest_text(self.content_commitment)
@dataclass(frozen=True)
class WorldObservationV1(WorldDTO):
 observation_id:str;kind:Literal['ENTITY','ATTRIBUTE','RELATION','REVOKE'];subject:str;predicate:str;value:str;target:str;event_time:int;observed_at:int;valid_until:int;evidence:WorldEvidenceRefV1;schema:Literal['observation-v1']='observation-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.observation_id);identifier(self.subject);identifier(self.predicate)
  require(self.event_time<=self.observed_at and self.event_time<self.valid_until,'TIME')
  require(self.namespace==self.evidence.namespace,'EVIDENCE_SCOPE');require(len(self.value.encode())<=1024,'PAYLOAD')
  if self.kind=='RELATION':identifier(self.target)
  else:require(self.target=='','TARGET')
 @property
 def content_commitment(self):return commit('ObservedContent',dict(namespace=self.namespace,kind=self.kind,subject=self.subject,predicate=self.predicate,value=self.value,target=self.target,event_time=self.event_time,observed_at=self.observed_at,valid_until=self.valid_until))
@dataclass(frozen=True)
class WorldEventV1(WorldDTO):
 event_id:str;expected_revision:int;precondition_commitment:str;commit_time:int;observation:WorldObservationV1;schema:Literal['event-v1']='event-v1'
 def __post_init__(self):super().__post_init__();identifier(self.event_id);digest_text(self.precondition_commitment);require(self.namespace==self.observation.namespace,'SCOPE')
@dataclass(frozen=True)
class WorldAttributeV1(WorldDTO):
 entity_id:str;predicate:str;value:str;event_time:int;valid_until:int;evidence_id:str;schema:Literal['attribute-v1']='attribute-v1'
@dataclass(frozen=True)
class WorldRelationV1(WorldDTO):
 source:str;target:str;relation:str;event_time:int;valid_until:int;evidence_id:str;schema:Literal['relation-v1']='relation-v1'
@dataclass(frozen=True)
class WorldStateV1(WorldDTO):
 revision:int;commit_time:int;entities:tuple[WorldEntityV1,...];attributes:tuple[WorldAttributeV1,...];relations:tuple[WorldRelationV1,...];revoked_evidence:tuple[str,...];schema:Literal['state-v1']='state-v1'
 def __post_init__(self):
  super().__post_init__();ids={e.entity_id for e in self.entities};require(len(ids)==len(self.entities),'ENTITY_DUPLICATE')
  require(all(x.namespace==self.namespace for x in self.entities+self.attributes+self.relations),'NESTED_NAMESPACE')
  require(all(a.entity_id in ids and a.event_time<a.valid_until for a in self.attributes),'ATTRIBUTE_BINDING')
  require(all(e.source in ids and e.target in ids and e.event_time<e.valid_until for e in self.relations),'RELATION_BINDING')
@dataclass(frozen=True)
class WorldStateRevisionV1(WorldDTO):
 revision:int;state_commitment:str;previous_commitment:str;event_commitment:str;schema:Literal['state-revision-v1']='state-revision-v1'
@dataclass(frozen=True)
class WorldHypothesisV1(WorldDTO):
 variable:str;operator:Literal['CONST','COPY','NOT','AND','OR'];parents:tuple[str,...];constant:int;assumptions:tuple[str,...];schema:Literal['hypothesis-v1']='hypothesis-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.variable);require(self.constant in (0,1),'BOOLEAN_VALUE');require(self.epistemic=='HYPOTHESIZED','MODEL_STATUS')
  for p in self.parents:identifier(p)
@dataclass(frozen=True)
class WorldCausalEdgeV1(WorldDTO):
 source:str;target:str;claim:Literal['CORRELATION','TEMPORAL_PRECEDENCE','HYPOTHESIZED_CAUSATION'];confounders:tuple[str,...];schema:Literal['causal-edge-v1']='causal-edge-v1'
@dataclass(frozen=True)
class WorldInterventionV1(WorldDTO):
 target:str;value:int;schema:Literal['intervention-v1']='intervention-v1'
 def __post_init__(self):super().__post_init__();identifier(self.target);require(self.value in (0,1) and self.epistemic=='HYPOTHESIZED','INTERVENTION')
@dataclass(frozen=True)
class WorldCounterfactualV1(WorldDTO):
 model_version:str;state_commitment:str;assignments:tuple[str,...];assumptions:tuple[str,...];status:Literal['HYPOTHETICAL','NOT_IDENTIFIABLE'];schema:Literal['counterfactual-v1']='counterfactual-v1'
@dataclass(frozen=True)
class WorldPredictionV1(WorldDTO):
 model_version:str;state_commitment:str;assignments:tuple[str,...];assumptions:tuple[str,...];uncertainty:Literal['UNCALIBRATED'];schema:Literal['prediction-v1']='prediction-v1'
@dataclass(frozen=True)
class WorldConflictV1(WorldDTO):
 subject:str;predicate:str;values:tuple[str,...];schema:Literal['conflict-v1']='conflict-v1'
@dataclass(frozen=True)
class WorldQueryV1(WorldDTO):
 entity_id:str;depth:int;limit:int;as_of:int;schema:Literal['query-v1']='query-v1'
 def __post_init__(self):super().__post_init__();identifier(self.entity_id);require(0<=self.depth<=8 and 1<=self.limit<=64,'QUERY_BOUND')
@dataclass(frozen=True)
class WorldReasoningResultV1(WorldDTO):
 model_version:str;state_commitment:str;status:Literal['HYPOTHETICAL','NOT_IDENTIFIABLE'];assignments:tuple[str,...];assumptions:tuple[str,...];alternatives:tuple[str,...];schema:Literal['reasoning-v1']='reasoning-v1'
@dataclass(frozen=True)
class CausalModelV1(WorldDTO):
 model_version:str;equations:tuple[WorldHypothesisV1,...];assumptions:tuple[str,...];confounders:tuple[str,...];alternatives:tuple[str,...];schema:Literal['causal-model-v1']='causal-model-v1'
 def __post_init__(self):super().__post_init__();identifier(self.model_version);require(1<=len(self.equations)<=32 and self.epistemic=='HYPOTHESIZED','MODEL_LIMIT')
