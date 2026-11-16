from .cases import validate,mapped
from skynet_autonomy_validation.reference import expected as auto
from skynet_adaptation_validation.benchmark import reference as adapt
from skynet_memory_validation.benchmark import reference as memory
from skynet_metacognition_validation.benchmark import reference as meta
OWN={'schema':'UNSUPPORTED_VERSION','missing_field':'TypeError','wrong_type':'INVALID_SCHEMA','unsupported':'ValueError:OPERATION','arity':'COMMAND_ARITY','concurrency':'COMMAND_VALUE','queue':'QUEUE_FULL'}
def expected(t):
 validate(t)
 if t['track']=='native':return None
 k=t['input']['kind']
 if k in OWN:return {'code':OWN[k],'protected_state_unchanged':True}
 m=mapped(t);return {'AUTO':auto,'ADAPT':adapt,'MEM':memory,'META':meta}[m['domain'].split('-')[0]](m)
