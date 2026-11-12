from cognitive_world_contracts import *
from cognitive_memory_retrieval import retrieve
from cognitive_world_transitions import apply_event

def observation_from_memory(memory_store,query,memory_id,observed_at):
 result=retrieve(memory_store,query);matches=[x for x in result.records if x.record.memory_id==memory_id];require(len(matches)==1,'MEMORY_NOT_CURRENT');m=matches[0];r=m.record
 args=(r.namespace,(m.commitment,),'OBSERVED','UNVERIFIED');e=WorldEvidenceRefV1(*args,'mem_'+r.memory_id,'0'*64,False)
 from dataclasses import replace
 o=WorldObservationV1(*args,'obs_'+r.memory_id,'ATTRIBUTE',r.subject,r.predicate,r.value,'',r.created_at,observed_at,r.expires_at,e)
 return replace(o,evidence=replace(e,content_commitment=o.content_commitment))
def validate_with_world(memory_store,query,world_state,reasoning,state,request,response):
 require(world_state.namespace==query.namespace==reasoning.namespace,'SCOPE');require(reasoning.state_commitment==world_state.commitment,'STALE_REASONING')
 # Re-read memory. Sidecars are labelled data, never alterations of trusted planner input.
 context=retrieve(memory_store,query)
 body=dict(memory=asdict(context),world_commitment=world_state.commitment,reasoning=asdict(reasoning),authoritative=False)
 require(len(canonical(body))<=8192,'CONTEXT_LIMIT')
 from cognitive_model_planning import validate_model_plan
 decision=validate_model_plan(state,request,response)
 return context,decision,commit('PlannerContextV1',body)
