from itertools import permutations
from cognitive_transfer_contracts import *
from cognitive_transfer_mapping import validate_mapping
from cognitive_transfer_abstraction import abstract
def discover(source,target,search_limit=720):
 abstract(source);abstract(target);typed(search_limit,int);require(1<=search_limit<=720,'SEARCH_BOUND');require(source.namespace==target.namespace,'NAMESPACE');require(len(source.entities)==len(target.entities),'UNMAPPED_CONCEPT');a=tuple(sorted(e.entity_id for e in source.entities));b=tuple(sorted(e.entity_id for e in target.entities));valid=[]
 for i,perm in enumerate(permutations(b)):
  require(i<search_limit,'SEARCH_EXHAUSTED');m=ConceptMappingV1(source.namespace,(source.commitment,target.commitment),'TEST_ONLY',source.commitment,target.commitment,a,perm)
  try:validate_mapping(source,target,m)
  except TransferError:continue
  valid.append(m)
 require(bool(valid),'NO_COMPATIBLE_MAPPING');return AnalogyCandidateV1(source.namespace,(source.commitment,target.commitment),'TEST_ONLY',valid[0],len(a)+len(source.relations),len(valid))
