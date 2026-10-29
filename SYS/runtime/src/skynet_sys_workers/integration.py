from copy import deepcopy
from skynet_sys.messages import Message
from skynet_sys.canonical import FrozenJSON,digest,check
from skynet_sys.evidence import EvidenceReference
from skynet_sys.tasks import TaskRequest
from skynet_sys_memory import MemoryError,Operation
from .orchestrator import need,Orchestrator,WorkerError
class Integrated:
 """Exclusive serial host-owned copies. No durable or external atomicity."""
 def __init__(self,core,scheduler,bus,memory,actor='admin',namespace='agent'):
  self.core=deepcopy(core);self.scheduler=deepcopy(scheduler);self.bus=deepcopy(bus);self.memory=deepcopy(memory);self.actor=actor;self.namespace=namespace;self.bindings={};self.commands=();self._seed=deepcopy((core,scheduler,bus,memory));self._checkpoint_version=0
  try:self._checkpoint_version=self.memory.read(actor,namespace,'workers').version
  except MemoryError as e:
   if str(e)!='MISSING':raise
 def _rows(self):
  cp=self.scheduler.checkpoint(self.actor);cp.verify();rows={}
  for value in cp.tasks:
   r=value.value();need(type(r) is list and len(r)==14 and type(r[0]) is str and r[0] not in rows,'SCHEDULER_LAYOUT');rows[r[0]]=r
  return rows
 def _capability(self,task,row):
  # SYS-003 public checkpoint supplies request digest but no capability field.
  try:
   state=self.scheduler._state;need(type(state) is dict and type(state.get('tasks')) is dict,'SCHEDULER_LAYOUT');entry=state['tasks'][task];need(type(entry) is dict,'SCHEDULER_LAYOUT');request=entry['request'];check(request,TaskRequest);need(request.task_id==task and request.commitment==row[1],'SCHEDULER_LAYOUT');return request.capability_required
  except (KeyError,TypeError,AttributeError,ValueError):raise WorkerError('SCHEDULER_LAYOUT') from None
 def _event(self,kind,subject,data,tick,index):
  payload=FrozenJSON.make({'schema_version':'sys005-events-v1','event':kind,'subject_id':subject,'data':data,'core_digest':self.core.state_digest(),'operation_sequence':len(self.commands),'event_index':index})
  msg=Message('workers:'+str(len(self.commands))+':'+str(index),'worker-trace',None,None,self.actor,self.bus.config.bus_id,'EVIDENCE_ATTACHED',payload,self.bus.config.at(tick),self.bus.config.at(tick+1));self.bus.publish(self.actor,'system.audit',msg,tick)
 def _checkpoint(self,tick,events):
  seq=len(self.commands);need(len(events)<=15,'EVENT_CAPACITY');ops=[]
  for index,(kind,subject,data) in enumerate(events):
   key='e:'+str(seq)+':'+str(index);payload=FrozenJSON.make({'event':kind,'subject_id':subject,'data':data,'logical_tick':tick,'sequence':seq,'event_index':index});h=digest('worker-provenance-v1',payload);ref=EvidenceReference(key,self.actor,subject,h,'worker-diagnostic',self.bus.config.at(tick),'UNVERIFIED');ops.append(Operation(self.namespace,key,'CREATE',0,payload,(ref,),'worker-evidence'))
  payload=FrozenJSON.make({'orchestration_digest':self.core.state_digest(),'journal_head':self.core.journal[-1].entry_hash if self.core.journal else self.core.seed,'scheduler_commitment':self.scheduler.checkpoint(self.actor).commitment})
  ops.append(Operation(self.namespace,'workers','CREATE' if self._checkpoint_version==0 else 'UPDATE',self._checkpoint_version,payload));self.memory.transact(self.actor,'workers:'+str(seq),tuple(ops),tick);self._checkpoint_version+=1
 def register(self,w,identity,tick):return self._run('register',(w,identity,tick))
 def activate(self,wid,tick):return self._run('activate',(wid,tick))
 def disable(self,wid,tick):return self._run('disable',(wid,tick))
 def cancel(self,lid,tick):return self._run('cancel',(lid,tick))
 def revoke(self,lid,tick):return self._run('revoke',(lid,tick))
 def dispatch(self,task,domain,cost,tick):return self._run('dispatch',(task,domain,cost,tick))
 def complete(self,actor,lid,attempt,domain,result,tick):return self._run('complete',(actor,lid,attempt,domain,result,tick))
 def fail_worker(self,wid,tick):return self._run('fail_worker',(wid,tick))
 def advance(self,tick):return self._run('advance',(tick,))
 def _run(self,op,args):
  need(len(self.commands)<64,'INTEGRATION_CAPACITY');d=deepcopy(self);d._noop=False;result=d._apply(op,args)
  if d._noop:return result
  del d._noop;d.commands+=((op,args),);self.__dict__.update(d.__dict__);return result
 def _terminal(self,lid,op,tick,events):
  need(lid in self.bindings and lid in self.core.leases,'UNKNOWN_LEASE');l=self.core.leases[lid];task,assignment=self.bindings[lid];row=self._rows().get(task);need(row is not None and row[8]==l.worker_id and row[9]==assignment,'STALE_ASSIGNMENT')
  target='CANCELLED' if op=='cancel' else 'REVOKED'
  if l.lease_state==target:
   need(row[11]=='CANCELLED','SCHEDULER_DIVERGENCE');self._noop=True;return
  need(l.lease_state=='ACTIVE','LEASE_STATE');getattr(self.core,op)(self.actor,lid,tick);self.scheduler.cancel(self.actor,task,tick);events.append(('TASK_CANCELLED' if op=='cancel' else 'LEASE_REVOKED',task,{'lease_id':lid,'worker_id':l.worker_id,'attempt':l.attempt,'state':target}))
 def _apply(self,op,args):
  tick=args[-1];events=[];result=None;self.core._pre(tick)
  if op=='register':
   w,identity,_=args;need(w.worker_id==identity.worker_id and w.capabilities==identity.capability_set,'IDENTITY');self.core.register(self.actor,w,tick);registered=self.core.workers[w.worker_id];events.append(('WORKER_REGISTERED',w.worker_id,{'worker_commitment':registered.commitment}));self.core.lifecycle(self.actor,w.worker_id,'AVAILABLE',tick);self.scheduler.register(self.actor,identity,w.resource_limits.active,tick);events.append(('WORKER_AVAILABLE',w.worker_id,{'worker_commitment':self.core.workers[w.worker_id].commitment}))
  elif op=='activate':
   wid,_=args;need(wid in self.core.workers,'UNKNOWN_WORKER');need(self.core.workers[wid].lifecycle_state in ('REGISTERED','UNAVAILABLE'),'STATE');self.core.lifecycle(self.actor,wid,'AVAILABLE',tick);self.scheduler.worker_state(self.actor,wid,'AVAILABLE',tick);events.append(('WORKER_AVAILABLE',wid,{'worker_commitment':self.core.workers[wid].commitment}))
  elif op in ('cancel','revoke'):
   self.core._admin(self.actor);self._terminal(args[0],op,tick,events)
   if self._noop:return None
  elif op=='disable':
   wid,_=args;self.core._admin(self.actor);need(wid in self.core.workers,'UNKNOWN_WORKER');need(self.core.workers[wid].lifecycle_state!='DISABLED','DISABLED')
   for lid,l in sorted(self.core.leases.items()):
    if l.worker_id==wid and l.lease_state=='ACTIVE':self._terminal(lid,'revoke',tick,events)
   self.core.lifecycle(self.actor,wid,'DISABLED',tick);self.scheduler.worker_state(self.actor,wid,'DISABLED',tick);events.append(('WORKER_DISABLED',wid,{'worker_commitment':self.core.workers[wid].commitment}))
  elif op=='dispatch':
   task,domain,cost,_=args;before=self._rows();need(task in before and before[task][11]=='READY','TASK_INELIGIBLE');cap=self._capability(task,before[task]);self.scheduler.dispatch(self.actor,tick,1);row=self._rows()[task];need(row[11]=='RUNNING','SCHEDULER_SELECTION');wid=row[8];need(wid in self.core.workers,'UNKNOWN_WORKER');result=self.core.assign(self.actor,wid,task,domain,cap,row[7],tick,row[10]-tick,cost);self.bindings[result.lease_id]=(task,row[9]);events.append(('WORKER_ASSIGNED',task,{'lease_id':result.lease_id,'lease_commitment':digest('issued-lease-v1',result),'worker_id':wid}))
  elif op=='complete':
   actor,lid,attempt,domain,payload,_=args;need(lid in self.bindings,'UNKNOWN_LEASE');duplicate=self.core.leases[lid].lease_state=='COMPLETED';result=self.core.complete(actor,lid,attempt,domain,payload,tick);task,assignment=self.bindings[lid];self.scheduler.complete(actor,task,assignment,True,tick)
   if duplicate:self._noop=True;return result
   events.append(('WORKER_COMPLETED',task,{'lease_id':lid,'worker_id':actor,'result_commitment':result}))
  elif op=='fail_worker':
   wid,_=args;self.core._admin(self.actor);need(wid in self.core.workers,'UNKNOWN_WORKER');need(self.core.workers[wid].lifecycle_state not in ('DISABLED','UNAVAILABLE'),'STATE');affected=[]
   for lid,l in sorted(self.core.leases.items()):
    if l.worker_id==wid and l.lease_state=='ACTIVE':
     task,assignment=self.bindings[lid];self.scheduler.complete(wid,task,assignment,False,tick);affected.append(lid)
   self.core.fail_worker(self.actor,wid,tick);self.scheduler.worker_state(self.actor,wid,'UNAVAILABLE',tick);events.append(('WORKER_FAILED',wid,{'leases':affected,'worker_commitment':self.core.workers[wid].commitment}))
  elif op=='advance':
   expired=sorted(lid for lid,l in self.core.leases.items() if l.lease_state=='ACTIVE' and tick>=l.expires_tick);self.core.advance(self.actor,tick);self.scheduler.advance(self.actor,tick)
   if expired:events.append(('LEASE_EXPIRED',self.actor,{'lease_ids':expired}))
  else:raise ValueError('OPERATION')
  self._checkpoint(tick,events)
  for index,(kind,subject,data) in enumerate(events):self._event(kind,subject,data,tick,index)
  return result
 def state_digest(self):return digest('integrated-workers-v2',(self.core.state_digest(),self.scheduler.checkpoint(self.actor).commitment,self.memory.digest(),self.bus._state_digest(self.bus._s),self._checkpoint_version,digest('lease-bindings-v1',tuple(sorted(self.bindings.items())))))
 def replay(self):
  out=Integrated(*self._seed,actor=self.actor,namespace=self.namespace)
  for op,args in self.commands:out._run(op,args)
  need(out.state_digest()==self.state_digest(),'REPLAY_MISMATCH');return out
