from cognitive_meta_contracts import *
from cognitive_meta_tracing import collect
from cognitive_meta_policy import decide
from cognitive_memory_retrieval import retrieve
from cognitive_world_epistemics import current_attributes
from cognitive_causal_engine import reason
from cognitive_model_planning import validate_model_plan

def observe_runtime(memory_store,memory_query,world_store,world_namespace,model,state,planning_request,raw_response,budget,requested_memory_ids=(),expected_world_revision=None):
 require(type(budget) is MetaBudgetV1,'BUDGET');budget.__post_init__();require(budget.namespace==memory_query.namespace==world_namespace==model.namespace,'CROSS_NAMESPACE_ACCESS');require(type(requested_memory_ids) is tuple and len(requested_memory_ids)<=64,'MEMORY_IDS')
 for x in requested_memory_ids:identifier(x)
 events=[];now=memory_query.now
 def add(kind,source,outcome,input_hash,output_hash):
  events.append(MetaEventV1(budget.namespace,budget.trace_id,now,source,(output_hash,),'OBSERVED','UNVERIFIED','e'+str(len(events)),len(events),kind,outcome,input_hash,output_hash,(len(events)+1,0,0,0,0)))
 add('PLAN_START','RUNTIME','OK',planning_request.request_binding,planning_request.request_binding)
 memory=retrieve(memory_store,memory_query);heads={x.record.memory_id:x for x in memory_store.snapshot()};available={x.record.memory_id for x in memory.records}
 outcome='OK'
 if memory.conflicts:outcome='CONFLICT'
 elif any(x in heads and heads[x].state=='REVOKED' for x in requested_memory_ids):outcome='REVOKED'
 elif any(x in heads and heads[x].record.expires_at<=now for x in requested_memory_ids):outcome='STALE'
 elif any(x not in available for x in requested_memory_ids):outcome='MISSING'
 add('MEMORY','MEMORY',outcome,memory_query.commitment,memory.commitment)
 world=world_store.state(world_namespace);_,conflicts=current_attributes(world,now)
 outcome='CONFLICT' if conflicts else ('STALE' if expected_world_revision is not None and world.revision!=expected_world_revision else 'OK')
 # Detect named memory-derived evidence whose source is no longer current.
 if any(a.evidence_id.startswith('mem_') and a.evidence_id[4:] not in available for a in world.attributes):outcome='REVOKED'
 add('WORLD','WORLD',outcome,world.commitment,world.commitment)
 causal=reason(model,world.commitment);add('CAUSAL','CAUSAL','HYPOTHETICAL' if causal.status=='HYPOTHETICAL' else 'NOT_IDENTIFIABLE',world.commitment,causal.commitment)
 # Actual predecessor validation; never accept a caller-provided successful decision.
 validation=validate_model_plan(state,planning_request,raw_response)
 add('PLAN_RESULT','PLANNER','OK' if validation.status=='MODEL_PLAN_ACCEPTED_ISOLATED' else 'REJECTED',planning_request.request_binding,validation.response_commitment)
 add('END','RUNTIME','OK',validation.response_commitment,validation.response_commitment)
 trace=collect(budget.namespace,budget.trace_id,now,tuple(events));return trace,decide(trace,budget),validation
