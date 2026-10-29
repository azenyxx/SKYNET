from cognitive_transfer_contracts import *
REQUIRED={'DAG':{'DEPENDENCIES'},'FLOW':{'CONSERVATION','CAPACITY'},'CAUSAL':{'INTERVENTION_REQUIRED'},'STATE':{'AUTHORIZATION','GUARDS'}}
RELATION={'DAG':'PRECEDES','FLOW':'FLOWS','CAUSAL':'CAUSES','STATE':'TRANSITIONS'}
def abstract(d):
 require(type(d) is DomainSchemaV1,'DOMAIN_TYPE');d.__post_init__();require(REQUIRED[d.kind]<={c.kind for c in d.constraints},'MISSING_CONSTRAINT');require(all(r.relation==RELATION[d.kind] for r in d.relations),'RELATION_TYPE')
 # Labels are retained for explicit correspondence, never scored as similarity.
 return AbstractPatternV1(d.namespace,(d.commitment,),'TEST_ONLY',d.commitment,d.kind,tuple(e.role for e in sorted(d.entities,key=lambda e:e.entity_id)),d.relations,d.constraints,('physical_semantics_not_represented',))
