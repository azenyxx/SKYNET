"""Reuse actual prior adapters for supplied graphs/rules, no new planner."""
import inspect,hashlib
from .cases import mapped
from skynet.system import System,T
from skynet_sys.canonical import FrozenJSON
from skynet_sys.tasks import TaskRequest
from skynet_sys_workers import Orchestrator
from skynet_sys_scheduler.scheduler import Scheduler
from skynet_planning_validation.adapter import execute as workflow
from skynet_adaptation_validation.adapter import execute as operational
from skynet_validation.registry import registry
from skynet_validation.evidence import commitment

def discover():
 objects={'System.run':System.run,'System._apply':System._apply,'Scheduler.dispatch':Scheduler.dispatch,'Orchestrator.complete':Orchestrator.complete,'registry':registry};body={'classification':'UNAVAILABLE','scope':'Supplied reference-system exported interfaces','sources':{k:hashlib.sha256(inspect.getsource(v).encode()).hexdigest() for k,v in objects.items()},'reason':'System requires host commands and supplied task graph/result payload. Scheduler selects eligible workers; no high-level goal interpreter, native planner or independent strategy revision interface.'};return dict(body,commitment=commitment('val008-admission',body))
def execute(t):
 d=t['domain'];x=t['input'];k=x['kind']
 if t['track']=='native':raise ValueError('NATIVE_INTERFACE_UNAVAILABLE')
 if d=='AUTO-003' or d=='AUTO-004' or (d=='AUTO-005' and k in('worker_failure','requeue','release','exhausted')):
  o=workflow(mapped(t)) if d=='AUTO-003' else operational(mapped(t));return {'status':o['status'],'answer':o['answer'],'calls':o['calls'],'details':{'observations':o['details'],'supplied_plan':mapped(t),'action_origin':'HOST','result_payload_origin':'HOST'},'classification':'INFRASTRUCTURE_AUTOMATION'}
 h=System(1,1);calls=[];details={}
 if d=='AUTO-001':
  if k=='duplicate':h.run('admit');calls.append('System.run.admit')
  before=h.scheduler.checkpoint('admin').commitment;code='OK'
  try:
   q=TaskRequest('invalid id' if k=='invalid_id' else 't0',None,'trace','admin','cognitive.reason',FrozenJSON.make({'value':x['value']}),0,'2026-10-25T00:01:00.000000Z','key:0',T);calls.append('Scheduler.admit');h.scheduler.admit('intruder' if k=='unauthorized' else 'admin',((q,('absent',) if k=='missing' else (),3),),0)
  except ValueError as e:code=str(e);calls.append('TaskRequest/ Scheduler rejection')
  after=h.scheduler.checkpoint('admin').commitment;answer={'code':code,'unchanged_on_rejection':None if code=='OK' else before==after,'admitted':len(h.rows())};details={'before':before,'after':after,'task_ids':list(h.rows())}
 else:
  h.run('admit');calls=['System.run.admit']
  if k=='unavailable':h.scheduler.worker_state('admin','w0','UNAVAILABLE',0);calls.append('Scheduler.worker_state')
  h.run('dispatch',1);calls.append('System.run.dispatch');before=h.state_digest()
  if k=='unavailable':answer={'state':h.rows()['t0'][11],'leases':len(h.workers.leases),'selected_workers':[v[8] for v in h.rows().values() if v[11]=='RUNNING']}
  else:
   lid=h.leases['t0'];l=h.workers.leases[lid]
   if k=='complete':
    result=h.run('complete','t0');rec=h.memory.read('admin','agent','result:t0');answer={'state':h.rows()['t0'][11],'lease':h.workers.leases[lid].lease_state,'result_bound':result==h.workers.results[lid]==rec.evidence_refs[0].artifact_digest,'action_origin':'HOST'};calls+=['System.run.complete','Store.read'];details['memory_commitment']=rec.commitment
   elif k=='pending':answer={'state':h.rows()['t0'][11],'lease':h.workers.leases[lid].lease_state,'unchanged_without_commands':before==h.state_digest(),'action_origin':'HOST'};calls.append('Scheduler.checkpoint')
   elif k=='stale_attempt':
    try:h.workers.complete('w0',lid,l.attempt+1,'d0',FrozenJSON.make({}),0);code='ACCEPTED'
    except ValueError as e:code=str(e)
    calls.append('Orchestrator.complete(stale)');answer={'code':code,'unchanged':before==h.state_digest(),'state':h.rows()['t0'][11]}
   elif k=='lease_expired':
    try:h.workers.complete('w0',lid,l.attempt,'d0',FrozenJSON.make({}),5);code='ACCEPTED'
    except ValueError as e:code=str(e)
    h.workers.advance('admin',5);h.scheduler.advance('admin',5)
    try:h.workers.complete('w0',lid,l.attempt,'d0',FrozenJSON.make({}),5);post='ACCEPTED'
    except ValueError as e:post=str(e)
    calls+=['Orchestrator.complete(deadline)','Orchestrator.advance','Scheduler.advance','Orchestrator.complete(expired)'];answer={'state':h.rows()['t0'][11],'lease':h.workers.leases[lid].lease_state,'completion_code':code,'post_advance_code':post}
   else:
    component_before=(h.scheduler.checkpoint('admin').commitment,h.workers.state_digest())
    try:h.run('recover','RETRY','t0','invalid-retry');code='ACCEPTED'
    except ValueError as e:code=str(e)
    calls.append('RecoveryExecutor.RETRY(ineligible)');answer={'code':code,'components_unchanged':component_before==(h.scheduler.checkpoint('admin').commitment,h.workers.state_digest())};details['recovery_audit']=[v.audit_commitment for v in h.coordinator.records]
  details.update(before=before,after=h.state_digest(),task_rows={k:list(v) for k,v in h.rows().items()},result_payload_origin='HOST',action_origin='HOST')
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'classification':'INFRASTRUCTURE_AUTOMATION'}
