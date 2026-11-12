"""Only fixed API invocation/normalization. Never imports benchmark or scoring."""
from .evidence import validate_task,need,commitment

def execute(task):
 validate_task(task);d=task['domain'];x=task['input']
 if d in ('CAP-003','CAP-006','CAP-009','CAP-010'):
  need(set(x)=={'problem','instance','depth'} and type(x['instance'])is int and type(x['depth'])is int and 1<=x['depth']<=3,'INPUT')
  return {'status':'UNAVAILABLE','answer':None,'calls':[],'provenance_reference':None,'limitations':['No suitable cognitive execution interface; no solver substituted.']}
 from skynet.system import System,T
 from skynet_sys.canonical import FrozenJSON,digest
 from skynet_sys.evidence import EvidenceReference
 from skynet_sys_verification import VerificationRequest,VerificationAssessment
 from skynet_sys_memory import Operation,MemoryError
 from skynet_sys.tasks import TaskRequest
 calls=[];details={}
 if d in ('CAP-001','CAP-008'):
  need(set(x)=={'policy','votes','label'} and x['policy'] in ('single','quorum','all') and type(x['votes'])is list and len(x['votes'])<=3 and all(v in ('PASS','FAIL','INCONCLUSIVE') for v in x['votes']),'INPUT')
  h=System(1,1);payload=FrozenJSON.make({'label':x['label']});c=digest('worker-result-v1',payload);q=VerificationRequest('request','task',c,'w0',('STRUCTURE','EVIDENCE'),x['policy'],0);h.engine.open(q,payload);calls.append('skynet_sys_verification.Engine.open')
  statuses=[]
  for i,v in enumerate(x['votes']):
   ref=EvidenceReference('e'+str(i),'v'+str(i),'task',c,'diagnostic',T,'UNVERIFIED');a=VerificationAssessment('a'+str(i),'request','v'+str(i),v,(ref,),('EXTERNALLY_SUPPLIED',),0);h.engine.submit(a,0);statuses.append(ref.verification_status);calls.append('skynet_sys_verification.Engine.submit')
  dec=h.engine.evaluate('request',0);calls.append('skynet_sys_verification.Engine.evaluate');answer={'verdict':dec.final_verdict,'conflict':bool(dec.conflict_refs),'evidence_status':statuses};details={'decision':dec.decision_commitment,'engine_state':h.engine.state_digest(),'conflicts':[c.commitment for c in h.engine.conflict_records('request')]}
 elif d=='CAP-002':
  need(set(x)=={'count','task'} and type(x['count'])is int and 1<=x['count']<=9 and x['task'] in ['t'+str(i) for i in range(x['count'])],'INPUT');h=System(x['count'],x['count']);h.run('admit');h.run('dispatch',x['count']);result=h.run('complete',x['task']);dec=h.run('verify',x['task'],'single');row=h.rows()[x['task']];lease=h.workers.leases[h.leases[x['task']]];rec=h.memory.read('admin','agent','result:'+x['task']);answer={'scheduler':row[11],'worker':lease.lease_state,'decision':dec.final_verdict,'binding':result==h.workers.results[lease.lease_id]==rec.evidence_refs[0].artifact_digest};calls=['skynet.System.run.admit','skynet.System.run.dispatch','skynet.System.run.complete','skynet.System.run.verify','skynet_sys_memory.Store.read'];details={'state':h.state_digest(),'journal_head':h.head,'result':result,'record':rec.commitment,'decision':dec.decision_commitment}
 elif d=='CAP-004':
  need(set(x)=={'count','fail_first','label'} and type(x['count'])is int and 1<=x['count']<=9 and type(x['fail_first'])is bool,'INPUT');h=System(1,1);n=x['count'];batch=tuple((TaskRequest('g'+str(i),None,'trace','admin','cognitive.reason',FrozenJSON.make({'label':x['label']}),0,'2026-10-25T00:01:00.000000Z','gkey'+str(i),T),('g'+str(i-1),) if i else (),1) for i in range(n));h.scheduler.admit('admin',batch,0);calls.append('skynet_sys_scheduler.Scheduler.admit');initial=[h.rows()['g'+str(i)][11] for i in range(n)];trace=[]
  for i in range(n):
   h.scheduler.dispatch('admin',0,1);calls.append('skynet_sys_scheduler.Scheduler.dispatch');row=h.rows()['g'+str(i)]
   if row[11]!='RUNNING':break
   trace.append(row[0]);h.scheduler.complete(row[8],row[0],row[9],not x['fail_first'],0);calls.append('skynet_sys_scheduler.Scheduler.complete')
  answer={'states':[h.rows()['g'+str(i)][11] for i in range(n)],'initial':initial};details={'checkpoint':h.scheduler.checkpoint('admin').commitment,'execution_order':trace}
 elif d=='CAP-005':
  need(set(x)=={'value','record_id'} and type(x['value'])is int and 0<=x['value']<=1000000 and type(x['record_id'])is str,'INPUT');h=System(1,1);payload=FrozenJSON.make({'value':x['value']});ref=EvidenceReference('memory-evidence','admin',x['record_id'],digest('memory-content-v1',payload),'diagnostic',T,'UNVERIFIED');h.memory.transact('admin','create',(Operation('agent',x['record_id'],'CREATE',0,payload,(ref,)),),0);record=h.memory.read('admin','agent',x['record_id']);before=record.commitment;code=''
  try:h.memory.transact('admin','stale',(Operation('agent',x['record_id'],'UPDATE',0,payload,(ref,)),),0)
  except MemoryError as e:code=str(e)
  calls=['skynet_sys_memory.Store.transact','skynet_sys_memory.Store.read','skynet_sys_memory.Store.transact.stale'];after=h.memory.read('admin','agent',x['record_id']);answer={'value':record.payload.value()['value'],'version':record.version,'stale_code':code,'unchanged':before==after.commitment,'provenance_status':record.evidence_refs[0].verification_status};details={'record':record.commitment,'evidence':ref.commitment,'post_state':h.memory.digest()}
 elif d=='CAP-007':
  need(set(x)=={'action','operation_id'} and x['action']in('RETRY','RELEASE_LEASE'),'INPUT');h=System(1,1);h.run('admit');h.run('dispatch',1);old=h.workers.leases[h.leases['t0']];calls=['skynet.System.run.admit','skynet.System.run.dispatch']
  if x['action']=='RETRY':h.run('recover','REQUEUE','t0','queue:'+x['operation_id']);calls.append('skynet_sys_recovery.RecoveryExecutor.execute.REQUEUE')
  receipt=h.run('recover',x['action'],'t0',x['operation_id']);calls.append('skynet_sys_recovery.RecoveryExecutor.execute.'+x['action']);code=''
  try:h.workers.complete(old.worker_id,old.lease_id,old.attempt,'d0',FrozenJSON.make({}),0)
  except ValueError as e:code=str(e)
  calls.append('skynet_sys_workers.Orchestrator.complete.stale');answer={'scheduler':h.rows()['t0'][11],'old_lease':h.workers.leases[old.lease_id].lease_state,'new_attempt':h.workers.leases[h.leases['t0']].attempt,'stale_code':code};details={'recovery':receipt.audit_commitment,'state':h.state_digest()}
 else:raise ValueError('DOMAIN')
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'provenance_reference':commitment('val001-observation-v1',{'calls':calls,'details':details}),'limitations':['Externally supplied inputs and fixed procedures; not autonomous reasoning.','UNVERIFIED references remain structurally checked, not factually certified.']}
