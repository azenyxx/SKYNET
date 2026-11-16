"""V1 isolated contracts. Hash consistency never confers factual authority."""
from dataclasses import dataclass,fields,asdict
from typing import get_type_hints,get_origin,get_args,Literal
import json,hashlib,re
MAX=2**63-1
class MemoryErrorV1(ValueError):
 def __init__(self,code):self.code=code;super().__init__(code)
def require(ok,code):
 if not ok:raise MemoryErrorV1(code)
def identifier(x):require(type(x) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,96}',x) is not None,'IDENTIFIER')
def digest_text(x):require(type(x) is str and re.fullmatch('[0-9a-f]{64}',x) is not None,'DIGEST')
def typed(v,t):
 origin=get_origin(t)
 if origin is Literal:require(v in get_args(t) and type(v) is str,'ENUM')
 elif origin is tuple:
  require(type(v) is tuple and len(v)<=128,'TUPLE');[typed(x,get_args(t)[0]) for x in v]
 elif t is int:require(type(v) is int and 0<=v<=MAX,'INTEGER')
 elif t is str:require(type(v) is str and len(v.encode('utf-8'))<=4096,'STRING')
 elif t is bool:require(type(v) is bool,'BOOLEAN')
 else:require(type(v) is t,'TYPE');v.__post_init__()
class DTO:
 def __post_init__(self):
  for f in fields(self):typed(getattr(self,f.name),get_type_hints(type(self))[f.name])
 @property
 def commitment(self):return commitment(type(self).__name__,self)
def canonical(v):return json.dumps(asdict(v) if isinstance(v,DTO) else v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def commitment(domain,v):return hashlib.sha256(('SKYNET:COG010:'+domain+':v1\0').encode()+canonical(v)).hexdigest()
def _pairs(pairs):
 d={}
 for k,v in pairs:require(k not in d,'DUPLICATE_KEY');d[k]=v
 return d
def parse(cls,raw):
 require(type(raw) is bytes and len(raw)<=65536,'ENCODING')
 try:
  obj=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_float=lambda _: (_ for _ in ()).throw(MemoryErrorV1('NUMBER')),parse_constant=lambda _: (_ for _ in ()).throw(MemoryErrorV1('NUMBER')))
  def build(c,o):
   require(type(o) is dict and set(o)=={f.name for f in fields(c)},'FIELDS');h=get_type_hints(c);v={}
   for k,x in o.items():
    t=h[k]
    if get_origin(t) is tuple:
     require(type(x) is list,'TYPE');sub=get_args(t)[0];v[k]=tuple(build(sub,y) if isinstance(sub,type) and issubclass(sub,DTO) else y for y in x)
    elif isinstance(t,type) and issubclass(t,DTO):v[k]=build(t,x)
    else:v[k]=x
   return c(**v)
  out=build(cls,obj);require(canonical(out)==raw,'NONCANONICAL');return out
 except MemoryErrorV1:raise
 except (ValueError,TypeError,UnicodeError,RecursionError,KeyError):raise MemoryErrorV1('MALFORMED') from None
@dataclass(frozen=True)
class MemoryProvenanceV1(DTO):
 source_id:str;source_revision:int;classification:Literal['UNTRUSTED','TEST_ONLY'];schema:Literal['provenance-v1']='provenance-v1'
 def __post_init__(self):super().__post_init__();identifier(self.source_id)
@dataclass(frozen=True)
class MemoryEvidenceV1(DTO):
 evidence_id:str;content_commitment:str;provenance:MemoryProvenanceV1;revoked:bool;schema:Literal['evidence-v1']='evidence-v1'
 def __post_init__(self):super().__post_init__();identifier(self.evidence_id);digest_text(self.content_commitment)
@dataclass(frozen=True)
class MemoryRecordV1(DTO):
 memory_id:str;namespace:str;subject:str;predicate:str;value:str;created_at:int;expires_at:int;retain_until:int;trust:Literal['UNVERIFIED','PROVISIONAL','VERIFIED','REJECTED','REVOKED'];evidence:tuple[MemoryEvidenceV1,...];schema:Literal['memory-v1']='memory-v1'
 def __post_init__(self):
  super().__post_init__()
  for s in (self.memory_id,self.namespace,self.subject,self.predicate):identifier(s)
  require(self.created_at<self.expires_at and self.retain_until>=self.created_at,'TIME');require(1<=len(self.evidence)<=8,'EVIDENCE_LIMIT');require(len(canonical(self))<=16384,'RECORD_SIZE')
 @property
 def content_commitment(self):return commitment('Content',dict(namespace=self.namespace,subject=self.subject,predicate=self.predicate,value=self.value))
@dataclass(frozen=True)
class MemoryRevisionV1(DTO):
 record:MemoryRecordV1;revision:int;state:Literal['CREATED','ADMITTED','ACTIVE','SUPERSEDED','EXPIRED','REVOKED','TOMBSTONED'];timestamp:int;previous_commitment:str;schema:Literal['revision-v1']='revision-v1'
@dataclass(frozen=True)
class MemoryQueryV1(DTO):
 namespace:str;subject:str;limit:int;now:int;minimum_trust:Literal['UNVERIFIED','PROVISIONAL','VERIFIED'];schema:Literal['query-v1']='query-v1'
 def __post_init__(self):super().__post_init__();identifier(self.namespace);identifier(self.subject);require(1<=self.limit<=64,'QUERY_LIMIT')
@dataclass(frozen=True)
class MemoryConflictV1(DTO):
 namespace:str;subject:str;predicate:str;memory_ids:tuple[str,...];status:Literal['UNRESOLVED'];schema:Literal['conflict-v1']='conflict-v1'
@dataclass(frozen=True)
class MemoryRetrievalResultV1(DTO):
 records:tuple[MemoryRevisionV1,...];conflicts:tuple[MemoryConflictV1,...];snapshot_commitment:str;schema:Literal['retrieval-v1']='retrieval-v1'
@dataclass(frozen=True)
class MemoryConsolidationV1(DTO):
 source_commitments:tuple[str,...];content_commitment:str;status:Literal['PROPOSAL_ONLY'];schema:Literal['consolidation-v1']='consolidation-v1'
@dataclass(frozen=True)
class MemoryRetentionPolicyV1(DTO):
 retain_until:int;physical_erasure:Literal['DISABLED'];schema:Literal['retention-v1']='retention-v1'
@dataclass(frozen=True)
class LearningObservationV1(DTO):
 observation_id:str;dataset_commitment:str;prediction:str;expected:str;schema:Literal['observation-v1']='observation-v1'
@dataclass(frozen=True)
class LearningProposalV1(DTO):
 proposal_id:str;dataset_commitment:str;training_ids:tuple[str,...];evaluation_ids:tuple[str,...];baseline:tuple[str,...];candidate:tuple[str,...];labels:tuple[str,...];schema:Literal['proposal-v1']='proposal-v1'
@dataclass(frozen=True)
class LearningEvaluationV1(DTO):
 proposal_commitment:str;dataset_commitment:str;total:int;baseline_correct:int;candidate_correct:int;regressions:int;status:Literal['IMPROVEMENT_MEASURED','REGRESSION_REJECTED','NO_IMPROVEMENT'];schema:Literal['evaluation-v1']='evaluation-v1'
@dataclass(frozen=True)
class LearningPromotionV1(DTO):
 proposal_commitment:str;status:Literal['AUTHORITY_UNAVAILABLE'];schema:Literal['promotion-v1']='promotion-v1'
@dataclass(frozen=True)
class LearningRollbackV1(DTO):
 checkpoint_commitment:str;status:Literal['AUTHORITY_UNAVAILABLE'];schema:Literal['rollback-v1']='rollback-v1'
