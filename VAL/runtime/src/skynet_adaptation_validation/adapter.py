"""Observations through existing public APIs. No evaluator or strategy solver."""
from skynet.system import System,T
from skynet_sys.canonical import FrozenJSON
from skynet_sys.tasks import TaskRequest
from skynet_sys_scheduler.contracts import SchedulingError
from skynet_validation.registry import registry
from skynet_validation.evidence import commitment

def execute(t):
 x=t['input'];k=x['kind'];calls=[]
 if t['track']=='native':
  reg=registry();return {'status':'UNAVAILABLE','answer':None,'calls':[],'details':{'registry':[(r['capability_id'],r['measurement_kind']) for r in reg if r['capability_id']in('CAP-004','CAP-007','CAP-009')],'reason':'Scheduler selects eligible workers; Recovery.recover requires host-selected policy_id; System.run requires host action. No exported autonomous strategy selection/revision interface.','native_experiment_executed':False},'level':'NOT_DEMONSTRATED'}
 if k in ('worker_failure','requeue','release','exhausted'):
  base=System(1,1);base.run('admit');base.run('dispatch',1);base.run('complete','t0');baseline=base.rows()['t0'][11]
  h=System(1,1,attempts=1 if k=='exhausted' else 3);h.run('admit');h.run('dispatch',1);old=h.workers.leases[h.leases['t0']];initial={'scheduler':h.rows()['t0'][11],'worker':h.workers.workers['w0'].lifecycle_state,'lease':old.lease_state,'digest':h.state_digest()};calls=['System.run.admit','System.run.dispatch','System.run.complete(control)']
  if k=='worker_failure':h.run('fail_worker','w0');h.run('activate','w0');calls+=['System.run.fail_worker','System.run.activate']
  else:h.run('recover','RELEASE_LEASE' if k=='release' else 'REQUEUE','t0','change');calls.append('RecoveryExecutor.'+('RELEASE_LEASE' if k=='release' else 'REQUEUE'))
  changed={'scheduler':h.rows()['t0'][11],'lease':h.workers.leases[old.lease_id].lease_state,'digest':h.state_digest()};retry_accepted=None
  if k in ('worker_failure','requeue'):h.run('recover','RETRY','t0','retry');h.run('complete','t0');calls+=['RecoveryExecutor.RETRY','System.run.complete']
  elif k=='exhausted':
   try:h.run('recover','RETRY','t0','retry');retry_accepted=True
   except ValueError as e:retry_accepted=False;retry_reason=str(e)
   calls.append('RecoveryExecutor.RETRY(exhausted)')
  try:h.workers.complete(old.worker_id,old.lease_id,old.attempt,'d0',FrozenJSON.make({}),0);code='ACCEPTED'
  except ValueError as e:code=str(e)
  calls.append('Orchestrator.complete(stale)');answer={'baseline':baseline,'state':h.rows()['t0'][11],'attempt':h.workers.leases[h.leases['t0']].attempt,'stale_code':code}
  if k=='exhausted':answer['retry_accepted']=retry_accepted;answer['retry_reason']=retry_reason
  details={'initial':initial,'changed':changed,'final_digest':h.state_digest(),'recovery_receipts':[e.audit_commitment for e in h.coordinator.records],'retry_reason':retry_reason if k=='exhausted' else None,'action_origin':'HOST_SELECTED_PREDEFINED_RECOVERY'};level='PROGRAMMED_RESPONSE'
 else:
  def batch(kind):
   rows=[]
   for i in range(2):
    deps=()
    if kind in ('missing','combined_missing') and i==0:deps=('absent',)
    if kind in ('cycle','combined_cycle'):deps=('g'+str(1-i),)
    if kind=='combined_dependency' and i==1:deps=('g0',)
    q=TaskRequest('g'+str(i),None,'trace','admin','cognitive.reason',FrozenJSON.make({'marker':x['marker'],'task':i}),x['priority'] if i==1 and kind in('priority','combined_priority') else 0,'2026-10-25T00:01:00.000000Z','key:'+str(i),T)
    rows.append((q,deps,2))
   return tuple(rows)
  base=System(2,2);base.scheduler.admit('admin',batch('baseline'),0);base.scheduler.dispatch('admin',0,2);baseline_running=sum(v[11]=='RUNNING' for v in base.rows().values())
  h=System(2,2);initial=h.scheduler.checkpoint('admin').commitment;calls=['Scheduler.admit(control)','Scheduler.dispatch(control)'];conditions=[]
  if k in ('unavailable','reactivate'):
   for wid in ('w0','w1'):h.scheduler.worker_state('admin',wid,'UNAVAILABLE',0);conditions.append((wid,'UNAVAILABLE'));calls.append('Scheduler.worker_state')
  elif k in ('capacity','priority') or k.startswith('combined_'):h.scheduler.worker_state('admin','w0','UNAVAILABLE',0);conditions.append(('w0','UNAVAILABLE'));calls.append('Scheduler.worker_state')
  if k=='reactivate':
   for wid in ('w0','w1'):h.scheduler.worker_state('admin',wid,'AVAILABLE',0);conditions.append((wid,'AVAILABLE'));calls.append('Scheduler.worker_state')
  before=h.scheduler.checkpoint('admin').commitment
  try:
   if k=='invalid_status':h.scheduler.worker_state('admin','w0','IMPOSSIBLE',0)
   h.scheduler.admit('admin',batch(k),0);calls.append('Scheduler.admit');h.scheduler.dispatch('admin',0,2);calls.append('Scheduler.dispatch');rows=h.rows();answer={'running':sum(v[11]=='RUNNING' for v in rows.values()),'ready':sum(v[11]=='READY' for v in rows.values()),'selected':sorted(i for i,v in rows.items() if v[11]=='RUNNING'),'baseline_running':baseline_running}
   if k=='combined_dependency':answer['waiting']=sum(v[11]=='WAITING' for v in rows.values())
  except SchedulingError as e:answer={'code':str(e),'unchanged':h.scheduler.checkpoint('admin').commitment==before,'baseline_running':baseline_running};calls.append('Scheduler.worker_state(rejected)' if k=='invalid_status' else 'Scheduler.admit(rejected)')
  details={'initial':initial,'changed_conditions':conditions,'before_operation':before,'after_operation':h.scheduler.checkpoint('admin').commitment,'baseline_checkpoint':base.scheduler.checkpoint('admin').commitment,'task_rows':{k:list(v) for k,v in h.rows().items()},'action_origin':'HOST_CONDITIONS_NATIVE_SCHEDULER_RULES'};level='CONSTRAINED_SELECTION'
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'level':level}
