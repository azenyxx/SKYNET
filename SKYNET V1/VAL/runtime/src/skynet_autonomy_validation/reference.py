from .cases import validate,mapped
from skynet_planning_validation.benchmark import reference as workflow_reference
from skynet_adaptation_validation.benchmark import reference as operational_reference
def expected(t):
 validate(t);d=t['domain'];k=t['input']['kind']
 if t['track']=='native':return None
 if d=='AUTO-001':return {'code':{'valid':'OK','unauthorized':'AUTHORIZATION','duplicate':'DUPLICATE_TASK','missing':'UNKNOWN_DEPENDENCY','invalid_id':'INVALID_IDENTITY'}[k],'unchanged_on_rejection':None if k=='valid' else True,'admitted':1 if k in('valid','duplicate') else 0}
 if d=='AUTO-002':
  if k=='complete':return {'state':'SUCCEEDED','lease':'COMPLETED','result_bound':True,'action_origin':'HOST'}
  if k=='pending':return {'state':'RUNNING','lease':'ACTIVE','unchanged_without_commands':True,'action_origin':'HOST'}
  if k=='stale_attempt':return {'code':'STALE_ATTEMPT','unchanged':True,'state':'RUNNING'}
  return {'state':'READY','leases':0,'selected_workers':[]}
 if d=='AUTO-003':return workflow_reference(mapped(t))
 if d=='AUTO-004' or k in('worker_failure','requeue','release','exhausted'):return operational_reference(mapped(t))
 if k=='lease_expired':return {'state':'READY','lease':'EXPIRED','completion_code':'EXPIRED','post_advance_code':'LEASE_STATE'}
 return {'code':'ValueError:REJECTED:RETRY_STATE','components_unchanged':True}
