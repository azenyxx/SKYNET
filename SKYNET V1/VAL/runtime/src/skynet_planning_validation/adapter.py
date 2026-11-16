"""Real public calls only; reference graph evaluator is not imported."""
from .contracts import validate
from skynet_validation.evidence import commitment

def execute(t):
 validate(t);x=t['input'];d=t['domain'];n=x['count']
 if d=='PLAN-002':return {'status':'UNAVAILABLE','answer':None,'calls':[],'provenance':None,'reason':'No goal-to-subtasks API in inherited System/Scheduler; absence classified once in manifest.'}
 from skynet.system import System,T
 from skynet_sys.canonical import FrozenJSON,digest
 from skynet_sys.tasks import TaskRequest
 from skynet_sys_memory import Operation
 from skynet_sys.evidence import EvidenceReference
 from skynet_sys_scheduler.contracts import SchedulingError
 h=System(1,1);calls=[];details={}
 def request(i,payload):return TaskRequest('g'+str(i),None,'trace','admin','cognitive.reason',FrozenJSON.make(payload),x['priorities'][i],'2026-10-25T00:01:00.000000Z','key:'+str(i),T)
 if d=='PLAN-001':
  payload={'goal_id':x['goal_id'],'preconditions':['authorized'],'required_outcome':x['value'],'dependencies':['external'],'completion_criteria':'reported_success'};q=request(0,payload);answer=q.payload.value();calls=['skynet_sys.tasks.TaskRequest','skynet_sys.canonical.FrozenJSON'];details={'task_commitment':q.commitment,'note':'Opaque structured representation only; no interpretation or enforcement of goal predicates.'}
 elif d in ('PLAN-003','PLAN-004','PLAN-005'):
  batch=[]
  for i in range(n):
   deps=() if d=='PLAN-004' else (('g'+str(i-1),) if i else ())
   if i==0 and x['kind']=='cycle':deps=('g'+str(n-1),)
   if i==0 and x['kind']=='missing':deps=('absent',)
   batch.append((request(i,{'goal':x['goal_id'],'value':x['value']}),deps,1))
  before=h.scheduler.checkpoint('admin').commitment;code='OK'
  try:h.scheduler.admit('admin',tuple(batch),0)
  except SchedulingError as e:code=str(e)
  calls.append('skynet_sys_scheduler.Scheduler.admit');after=h.scheduler.checkpoint('admin').commitment
  if d=='PLAN-003':answer={'code':code,'accepted':code=='OK','unchanged_on_rejection':before==after if code!='OK' else None};details={'before':before,'after':after}
  elif d=='PLAN-004':
   if code!='OK':raise ValueError(code)
   if x['kind']=='unavailable':h.scheduler.worker_state('admin','w0','UNAVAILABLE',0);calls.append('skynet_sys_scheduler.Scheduler.worker_state')
   h.scheduler.dispatch('admin',0,n);calls.append('skynet_sys_scheduler.Scheduler.dispatch');rows=h.rows();answer={'states':[rows['g'+str(i)][11] for i in range(n)],'running':sum(v[11]=='RUNNING' for v in rows.values())};details={'checkpoint':h.scheduler.checkpoint('admin').commitment}
  else:
   if code!='OK':raise ValueError(code)
   completed=[];valid=True;failed=False
   for step in range(n):
    h.scheduler.dispatch('admin',0,1);calls.append('skynet_sys_scheduler.Scheduler.dispatch');running=[row for row in h.rows().values() if row[11]=='RUNNING']
    if not running:break
    row=running[0];valid=valid and all(h.rows()[dep][11]=='SUCCEEDED' for dep in row[2]);lease=h.workers.assign('admin',row[8],row[0],'d0','cognitive.reason',row[7],0,row[10],1);calls.append('skynet_sys_workers.Orchestrator.assign')
    if x['kind']=='failure':h.workers.fail_worker('admin',row[8],0);h.scheduler.complete(row[8],row[0],row[9],False,0);calls+=['skynet_sys_workers.Orchestrator.fail_worker','skynet_sys_scheduler.Scheduler.complete'];failed=True;break
    payload=FrozenJSON.make({'task':row[0],'goal':x['goal_id']});result=h.workers.complete(row[8],lease.lease_id,lease.attempt,'d0',payload,0);ref=EvidenceReference('e:'+row[0],row[8],row[0],result,'diagnostic',T,'UNVERIFIED');h.memory.transact('admin','tx:'+row[0],(Operation('agent',row[0],'CREATE',0,payload,(ref,)),),0);h.scheduler.complete(row[8],row[0],row[9],True,0);record=h.memory.read('admin','agent',row[0]);valid=valid and record.evidence_refs[0].artifact_digest==h.workers.results[lease.lease_id];completed.append({'task':row[0],'worker_result':result,'memory_commitment':record.commitment});calls+=['skynet_sys_workers.Orchestrator.complete','skynet_sys_memory.Store.transact','skynet_sys_scheduler.Scheduler.complete','skynet_sys_memory.Store.read']
   states=[h.rows()['g'+str(i)][11] for i in range(n)];answer={'states':states,'completed':len(completed),'dependency_preserved':valid,'failure_propagated':failed and all(s=='FAILED' for s in states)};details={'completed_results':completed,'scheduler':h.scheduler.checkpoint('admin').commitment,'workers':h.workers.state_digest(),'memory':h.memory.digest()}
 elif d=='PLAN-006':
  h.run('admit');h.run('dispatch',1);old=h.workers.leases[h.leases['t0']];calls=['skynet.System.run.admit','skynet.System.run.dispatch']
  if x['kind']=='worker_failure':h.run('fail_worker',old.worker_id);h.run('activate',old.worker_id);calls+=['skynet.System.run.fail_worker','skynet.System.run.activate']
  elif x['kind']=='requeue':h.run('recover','REQUEUE','t0','requeue');calls.append('skynet_sys_recovery.RecoveryExecutor.REQUEUE')
  if x['kind']=='release':h.run('recover','RELEASE_LEASE','t0','release');calls.append('skynet_sys_recovery.RecoveryExecutor.RELEASE_LEASE')
  else:h.run('recover','RETRY','t0','retry');h.run('complete','t0');calls+=['skynet_sys_recovery.RecoveryExecutor.RETRY','skynet.System.run.complete']
  code=''
  try:h.workers.complete(old.worker_id,old.lease_id,old.attempt,'d0',FrozenJSON.make({}),0)
  except ValueError as e:code=str(e)
  calls.append('skynet_sys_workers.Orchestrator.complete.stale');answer={'scheduler':h.rows()['t0'][11],'attempt':h.workers.leases[h.leases['t0']].attempt,'old_lease':h.workers.leases[old.lease_id].lease_state,'stale_code':code};details={'state':h.state_digest(),'recovery_receipts':[e.audit_commitment for e in h.coordinator.records]}
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'provenance':commitment('val003-observed',{'calls':calls,'details':details}),'limitation':'Externally supplied goal/graph/action. No autonomous decomposition or plan revision.'}
