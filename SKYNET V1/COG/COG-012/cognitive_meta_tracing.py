from cognitive_meta_contracts import *
STAGES=('PLAN_START','MEMORY','WORLD','CAUSAL','PLAN_RESULT','END')
SOURCES=dict(PLAN_START='RUNTIME',MEMORY='MEMORY',WORLD='WORLD',CAUSAL='CAUSAL',PLAN_RESULT='PLANNER',END='RUNTIME',RESOURCE='RUNTIME',ERROR='RUNTIME')
def validate_trace(trace):
 require(type(trace) is MetaTraceV1,'TRACE_TYPE');trace.__post_init__();require(1<=len(trace.events)<=128,'TRACE_LIMIT');require(len(canonical(trace))<=65536,'TRACE_SIZE')
 ids=set();last_time=0;last_usage=(0,)*5;stage=-1
 for i,e in enumerate(trace.events):
  require(e.namespace==trace.namespace and e.trace_id==trace.trace_id,'CROSS_NAMESPACE_ACCESS');require(e.sequence==i and e.event_id not in ids,'TRACE_SEQUENCE');ids.add(e.event_id)
  require(last_time<=e.timestamp<=trace.timestamp,'TRACE_TIME');require(e.source==SOURCES[e.kind],'SOURCE_BINDING');require(all(a<=b for a,b in zip(last_usage,e.usage)),'RESOURCE_COUNTER_REGRESSION')
  if e.kind in STAGES:
   n=STAGES.index(e.kind);require(n>stage,'TRACE_ORDER');stage=n
  last_time=e.timestamp;last_usage=e.usage
 return tuple(s for s in STAGES if s not in {e.kind for e in trace.events})
def collect(namespace,trace_id,timestamp,events):
 require(type(events) is tuple,'EVENTS_TYPE');t=MetaTraceV1(namespace,trace_id,timestamp,'RUNTIME',(),'OBSERVED','UNVERIFIED',events);validate_trace(t);return t
