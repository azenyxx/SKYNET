from cognitive_transfer_contracts import *
from cognitive_transfer_mapping import validate_mapping
STRATEGIES={'DAG':'TOPOLOGICAL','FLOW':'CONSERVE','CAUSAL':'INTERVENTION_ONLY','STATE':'GUARDED'}
def hypothesize(source,target,m):
 validate_mapping(source,target,m)
 return TransferHypothesisV1(source.namespace,(source.commitment,target.commitment,m.commitment),'TEST_ONLY',m,STRATEGIES[source.kind],tuple(sorted(set(source.assumptions+target.assumptions))),'TARGET_CONSTRAINT_OR_LABEL_MISMATCH','HYPOTHESIZED')
