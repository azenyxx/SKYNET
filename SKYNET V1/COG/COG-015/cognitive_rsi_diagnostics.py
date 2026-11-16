from cognitive_rsi_contracts import *
from cognitive_rsi_evaluation import observe
def diagnose(b,observation):
 require(type(observation) is ImprovementObservationV1,'OBSERVATION_TYPE');require(not observation.revoked,'REVOKED');require(observation==observe(b),'OBSERVATION_TAMPER');m=observation.metrics
 kind='FALSE_TRANSFER' if m.failures else ('REDUNDANT_WORK' if m.operations>m.total else 'NO_MEASURED_DEFICIENCY');severity='HIGH' if m.failures else ('MEDIUM' if kind=='REDUNDANT_WORK' else 'UNKNOWN')
 return ImprovementBottleneckV1(b.namespace,b.session_id,(observation.commitment,),'TEST_ONLY',observation.commitment,kind,severity)
