"""Native track intentionally has no solver. No oracle imports."""
from .contracts import validate,need,commitment
from skynet_validation.registry import registry

def execute(task,track='native_SKYNET'):
 validate(task);need(track in ('native_SKYNET','added_symbolic'),'TRACK')
 if track=='added_symbolic':return {'status':'NOT_TESTABLE','answer':None,'execution_interface':None,'reason':'TRACK_B_ABSENT','provenance_reference':None}
 # Registry is inherited actual VAL001 metadata, not a fabricated execution result.
 inherited=registry();assert len(inherited)==10
 return {'status':'UNAVAILABLE','answer':None,'execution_interface':None,'reason':'NO_NATIVE_SYMBOLIC_EXECUTION_CONTRACT','provenance_reference':None,'registry_commitment':commitment('val002-inherited-registry',inherited),'limitation':'SYS006 combines supplied assessments; scheduler executes supplied graphs. Neither accepts symbolic premises and infers a conclusion.'}
