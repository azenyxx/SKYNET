from cognitive_meta_contracts import *
from cognitive_meta_tracing import validate_trace
MAP={'REJECTED':('VALIDATOR_REJECTION','ERROR','STOP'),'MISSING':('MISSING_EVIDENCE','WARNING','REQUEST_EVIDENCE'),'REVOKED':('EVIDENCE_REVOKED','ERROR','ABSTAIN'),'STALE':('STALE_CONTEXT','WARNING','ABSTAIN'),'CONFLICT':('CONTRADICTION','ERROR','ABSTAIN'),'NOT_IDENTIFIABLE':('UNSUPPORTED_CAUSAL_CLAIM','WARNING','ABSTAIN'),'UNAUTHORIZED':('UNAUTHORIZED_ACTION','ERROR','STOP'),'UNSUPPORTED_CONFIDENCE':('CONFIDENCE_MISREPRESENTATION','ERROR','ABSTAIN'),'FACT_CLAIM':('CONFIDENCE_MISREPRESENTATION','ERROR','ABSTAIN'),'CORRELATION_CAUSAL':('UNSUPPORTED_CAUSAL_CLAIM','ERROR','ABSTAIN'),'UNKNOWN':('MISSING_EVIDENCE','WARNING','REQUEST_EVIDENCE')}
def monitor(trace,budget):
 missing=validate_trace(trace);require(type(budget) is MetaBudgetV1,'BUDGET_TYPE');budget.__post_init__();require((budget.namespace,budget.trace_id)==(trace.namespace,trace.trace_id),'BUDGET_SCOPE');out=[]
 def finding(code,severity,action,evidence,source='MONITOR'):
  out.append(MetaAnomalyV1(trace.namespace,trace.trace_id,trace.timestamp,source,(evidence,),'INFERRED','UNVERIFIED',code,severity,evidence,action))
 if missing:finding('INCOMPLETE_TRACE','ERROR','ABSTAIN',trace.commitment)
 for e in trace.events:
  if e.outcome in MAP:finding(*MAP[e.outcome],e.commitment,e.source)
  if e.kind not in ('PLAN_START','END','RESOURCE') and not e.evidence:finding('MISSING_EVIDENCE','WARNING','REQUEST_EVIDENCE',e.commitment,e.source)
  if e.kind=='ERROR':finding('INVALID_SCHEMA','ERROR','STOP',e.commitment)
 usage=trace.events[-1].usage
 if any(u>=limit for u,limit in zip(usage,budget.limits)):finding('RESOURCE_EXHAUSTION','ERROR','STOP',budget.commitment)
 if budget.retries_used>budget.retry_limit or (budget.retries_used==budget.retry_limit and (budget.retries_used>0 or any(x.code=='VALIDATOR_REJECTION' for x in out))):finding('RETRY_LIMIT','ERROR','STOP',budget.commitment)
 return tuple(out)
