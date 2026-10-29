from cognitive_memory_contracts import *
from cognitive_memory_retrieval import retrieve
def validate_with_memory(store,query,state,request,response):
 # Context is an explicitly untrusted sidecar. Existing COG008 has no context field.
 # Never rewrite the trusted objective, limits, permissions or model response.
 context=retrieve(store,query);raw=canonical(context);require(len(raw)<=8192,'CONTEXT_LIMIT')
 from cognitive_model_planning import validate_model_plan
 decision=validate_model_plan(state,request,response)
 return context,decision,commitment('PlannerSidecar',dict(context=context.commitment,request=request.request_binding,response=decision.response_commitment,authoritative=False))
