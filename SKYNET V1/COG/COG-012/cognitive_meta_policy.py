from cognitive_meta_contracts import *
from cognitive_meta_monitor import monitor
from cognitive_meta_uncertainty import assess_uncertainty
def decide(trace,budget,*,stop_latched=False):
 require(type(stop_latched) is bool,'LATCH_TYPE');fs=monitor(trace,budget);codes=tuple(sorted({f.code for f in fs}));actions={f.recommendation for f in fs}
 if stop_latched:action='STOP';codes=tuple(sorted(set(codes)|{'STOP_LATCHED'}))
 elif 'STOP' in actions:action='STOP'
 elif 'ABSTAIN' in actions:action='ABSTAIN'
 elif 'REQUEST_EVIDENCE' in actions:action='REQUEST_EVIDENCE'
 elif budget.retries_used:action='RECONSIDER'
 else:action='CONTINUE'
 return MetaDecisionV1(trace.namespace,trace.trace_id,trace.timestamp,'MONITOR',(trace.commitment,budget.commitment),'INFERRED','UNVERIFIED',action,codes,trace.commitment,budget.commitment,'meta-policy-v1')
