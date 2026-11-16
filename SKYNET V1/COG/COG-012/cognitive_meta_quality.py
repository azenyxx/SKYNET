from dataclasses import dataclass
from cognitive_meta_contracts import *
from cognitive_meta_monitor import monitor
@dataclass(frozen=True)
class QualityReportV1:
 trace_commitment:str;events:int;evidence_events:int;constraint_violations:tuple[str,...];unverified_concerns:tuple[str,...];factual_correctness:str='UNKNOWN'
def evaluate_quality(trace,budget):
 fs=monitor(trace,budget)
 return QualityReportV1(trace.commitment,len(trace.events),sum(bool(e.evidence) for e in trace.events),tuple(sorted({f.code for f in fs if f.code in ('RESOURCE_EXHAUSTION','RETRY_LIMIT','VALIDATOR_REJECTION','INCOMPLETE_TRACE')})),tuple(sorted({f.code for f in fs if f.code not in ('RESOURCE_EXHAUSTION','RETRY_LIMIT','VALIDATOR_REJECTION','INCOMPLETE_TRACE')})))
