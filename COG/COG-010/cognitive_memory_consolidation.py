from cognitive_memory_contracts import *
def propose_consolidation(store,namespace,ids):
 identifier(namespace);require(type(ids) is tuple and 2<=len(ids)<=64 and len(set(ids))==len(ids),'LINEAGE');history=store.snapshot();heads={x.record.memory_id:x for x in history}
 require(all(i in heads for i in ids),'NOT_FOUND');rs=[heads[i] for i in sorted(ids)]
 require(all(x.record.namespace==namespace and x.state=='ACTIVE' for x in rs),'SCOPE');require(len({x.record.content_commitment for x in rs})==1,'CONFLICT')
 return MemoryConsolidationV1(tuple(x.commitment for x in rs),rs[0].record.content_commitment,'PROPOSAL_ONLY')
