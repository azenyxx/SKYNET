"""Native absence admitted once. Public memory/recovery only; no learner."""
import inspect,hashlib
from skynet.system import System,T
from skynet_sys_memory.store import Store,Namespace,Operation,MemoryError
from skynet_sys.capabilities import HostPolicy
from skynet_sys.evidence import EvidenceReference
from skynet_sys.canonical import FrozenJSON,digest
from skynet_sys.errors import ContractError
from skynet_validation.registry import registry
from skynet_validation.evidence import commitment

def discover():
 # Evidence scoped to exported reference-system interfaces, not claims about unseen code.
 from skynet_sys_recovery.coordinated import RecoveryExecutor
 objects={'System.run':System.run,'System._apply':System._apply,'Store.transact':Store.transact,'RecoveryExecutor.execute':RecoveryExecutor.execute,'registry':registry}
 rows=registry();body={'classification':'UNAVAILABLE','scope':'Exported System/Store/RecoveryExecutor and inherited capability registry','sources':{n:hashlib.sha256(inspect.getsource(o).encode()).hexdigest() for n,o in objects.items()},'registry':[(r['capability_id'],r['measurement_kind'],r['limitations']) for r in rows if r['capability_id']in('CAP-005','CAP-006','CAP-007','CAP-009','CAP-010')],'reason':'No train/fit/learn/predict or experience-dependent execution contract. Store records supplied values; recovery requires host-selected action.'};return dict(body,commitment=commitment('val006-admission',body))
def execute(t):
 if t['track']!='infrastructure':raise ValueError('NATIVE_INTERFACE_UNAVAILABLE')
 x=t['input'];k=x['kind'];calls=[]
 def store():return Store(HostPolicy('policy',(('host','memory.read'),('host','memory.write'))),(Namespace('agent:experience','host',('host',),('host',)),))
 s=store();control=store();payload=FrozenJSON.make(x['experience']);ev=EvidenceReference('evidence','host',x['key'],digest('experience',payload),'reported-experience',T,'UNVERIFIED')
 def write(tx='initial',key=None,refs=None,value=None):
  calls.append('skynet_sys_memory.store.Store.transact');return s.transact('host',tx,(Operation('agent:experience',key or x['key'],'CREATE',0,value or payload,(ev,) if refs is None else refs),),0)
 def read(st=s,key=None):calls.append('skynet_sys_memory.store.Store.read');return st.read('host','agent:experience',key or x['key'])
 initial=s.digest();write();before=s.digest();details={'initial_memory_digest':initial,'after_experience_digest':before,'control_initial_digest':control.digest(),'actual_interface':'Store.transact/read; System.run for retry only'}
 try:read(control);control_status='FOUND'
 except MemoryError as e:control_status=str(e)
 error=None
 try:
  if k=='missing':read(key='absent')
  elif k=='invalid_id':write('invalid',key='invalid id')
  elif k=='bad_provenance':
   calls.append('skynet_sys.evidence.EvidenceReference');bad=EvidenceReference('bad','host',x['key'],'not-a-hash','reported-experience',T,'UNVERIFIED');write('bad',refs=(bad,))
  elif k=='duplicate_evidence':write('duplicate',key='another',refs=(ev,ev))
  elif k=='conflicting':write(value=FrozenJSON.make({'forged':True}))
 except (MemoryError,ContractError) as e:error=str(e);details['exception_type']=type(e).__name__
 rec=read();answer={'retained':rec.payload.value(),'verification_status':rec.evidence_refs[0].verification_status}
 if error:answer.update(rejection=error,memory_unchanged=s.digest()==before)
 elif k=='retry':
  h=System(1,1);h.run('admit');h.run('dispatch',1);old=h.workers.leases[h.leases['t0']];h.run('fail_worker','w0');details['failed_state']=h.rows()['t0'][11];h.run('activate','w0');h.run('recover','RETRY','t0','host-retry');h.run('complete','t0')
  try:h.workers.complete('w0',old.lease_id,old.attempt,'d0',FrozenJSON.make({}),0);code='ACCEPTED'
  except ValueError as e:code=str(e)
  answer.update(state=h.rows()['t0'][11],attempt=h.workers.leases[h.leases['t0']].attempt,stale_rejection=code,action_origin='HOST_SELECTED',learning=False);calls+=['System.run.admit','System.run.dispatch','System.run.fail_worker','System.run.activate','RecoveryExecutor.RETRY','System.run.complete','Orchestrator.complete(stale)'];details['recovery_receipts']=[v.audit_commitment for v in h.coordinator.records];details['system_digest']=h.state_digest()
 else:answer.update(control=control_status,learning=False)
 details.update(final_memory_digest=s.digest(),record_commitment=rec.commitment,evidence_commitment=ev.commitment,control_final_digest=control.digest(),control_result=control_status)
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'classification':'PROGRAMMED_RECOVERY' if k=='retry' else 'EXPERIENCE_STORAGE'}
