from cognitive_world_contracts import *
def empty(namespace):return WorldStateV1(namespace,('0'*64,),'UNKNOWN','UNVERIFIED',0,0,(),(),(),())
def apply_event(state,event):
 require(type(state) is WorldStateV1 and type(event) is WorldEventV1,'TYPE');state.__post_init__();event.__post_init__();o=event.observation;e=o.evidence
 require(event.namespace==state.namespace and event.expected_revision==state.revision,'STALE_REVISION');require(event.precondition_commitment==state.commitment,'PRECONDITION')
 require(event.commit_time>=max(state.commit_time,o.observed_at),'COMMIT_TIME');require(event.epistemic=='OBSERVED' and o.epistemic=='OBSERVED','OBSERVATION_ONLY')
 require(not e.revoked and e.evidence_id not in state.revoked_evidence,'EVIDENCE_REVOKED');require(e.content_commitment==o.content_commitment,'EVIDENCE_BINDING')
 entities=list(state.entities);attrs=list(state.attributes);rels=list(state.relations);rev=list(state.revoked_evidence);ids={x.entity_id for x in entities}
 args=(state.namespace,(e.commitment,),'OBSERVED','UNVERIFIED')
 if o.kind=='ENTITY':
  require(o.subject not in ids and len(ids)<128,'ENTITY_DUPLICATE_OR_LIMIT');identifier(o.value);entities.append(WorldEntityV1(*args,o.subject,o.value))
 else:
  require(o.subject in ids,'ENTITY_MISSING')
  if o.kind=='ATTRIBUTE':attrs.append(WorldAttributeV1(*args,o.subject,o.predicate,o.value,o.event_time,o.valid_until,e.evidence_id))
  elif o.kind=='RELATION':require(o.target in ids,'TARGET_MISSING');rels.append(WorldRelationV1(*args,o.subject,o.target,o.predicate,o.event_time,o.valid_until,e.evidence_id))
  elif o.kind=='REVOKE':
   identifier(o.value);require(o.value not in rev,'ALREADY_REVOKED');rev.append(o.value)
 require(len(attrs)<=128 and len(rels)<=128 and len(rev)<=128,'STATE_LIMIT')
 return WorldStateV1(state.namespace,(event.commitment,),'INFERRED','UNVERIFIED',state.revision+1,event.commit_time,tuple(sorted(entities,key=lambda x:x.entity_id)),tuple(attrs),tuple(rels),tuple(sorted(rev)))
