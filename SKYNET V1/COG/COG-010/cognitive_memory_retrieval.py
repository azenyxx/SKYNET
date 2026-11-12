from cognitive_memory_contracts import *
def retrieve(store,query):
 require(type(query) is MemoryQueryV1,'QUERY_TYPE');query.__post_init__();history=store.snapshot();heads={x.record.memory_id:x for x in history}
 pool=[x for x in heads.values() if x.state=='ACTIVE' and x.record.namespace==query.namespace and x.record.subject==query.subject and x.record.created_at<=query.now<x.record.expires_at]
 groups={}
 for x in pool:groups.setdefault(x.record.predicate,[]).append(x)
 conflicts=[];bad=set()
 for pred,rs in sorted(groups.items()):
  if len({x.record.value for x in rs})>1:
   ids=tuple(sorted(x.record.memory_id for x in rs));require(len(ids)<=128,'CONFLICT_LIMIT');conflicts.append(MemoryConflictV1(query.namespace,query.subject,pred,ids,'UNRESOLVED'));bad.update(ids)
 ranks={'UNVERIFIED':0,'PROVISIONAL':1,'VERIFIED':2};require(len(conflicts)<=128,'CONFLICT_LIMIT')
 eligible=[x for x in pool if x.record.memory_id not in bad and ranks.get(x.record.trust,-1)>=ranks[query.minimum_trust]]
 eligible.sort(key=lambda x:(-ranks[x.record.trust],-x.timestamp,x.record.memory_id))
 return MemoryRetrievalResultV1(tuple(eligible[:query.limit]),tuple(conflicts),commitment('Snapshot',[x.commitment for x in history]))
