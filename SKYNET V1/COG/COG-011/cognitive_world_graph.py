from cognitive_world_contracts import *
def traverse(state,query):
 require(type(state) is WorldStateV1 and type(query) is WorldQueryV1,'TYPE');state.__post_init__();query.__post_init__();require(state.namespace==query.namespace,'NAMESPACE')
 require(query.entity_id in {x.entity_id for x in state.entities},'ENTITY_MISSING');seen={query.entity_id};front=[query.entity_id];out=[]
 for _ in range(query.depth):
  nxt=[]
  for node in sorted(front):
   edges=sorted((e for e in state.relations if e.source==node and e.evidence_id not in state.revoked_evidence and e.event_time<=query.as_of<e.valid_until),key=lambda e:(e.relation,e.target,e.commitment))
   for e in edges:
    if e.target not in seen:seen.add(e.target);nxt.append(e.target);out.append(e.target)
    if len(out)>=query.limit:return tuple(out)
  front=nxt
  if not front:break
 return tuple(out)
