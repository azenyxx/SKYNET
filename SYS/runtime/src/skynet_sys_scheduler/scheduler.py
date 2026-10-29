from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from skynet_sys.tasks import TaskRequest
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.messages import Message
from skynet_sys.canonical import FrozenJSON,canonical,digest,check,ident
from skynet_sys_transport.bus import Bus
from skynet_sys_transport.contracts import collection_digest,nat
from .contracts import *
TOPIC='cognitive.tasks'
class Scheduler:
 def __init__(self,bus,policy,producer_id='p'):
  need(type(bus) is Bus and type(policy) is Policy,'INPUT');policy.__post_init__();ident(producer_id)
  self._seed=deepcopy(bus);self._bus=deepcopy(bus);self.policy=policy;self.producer_id=producer_id
  self._state={'tick':0,'sequence':0,'tasks':{},'workers':{}};self._journal=[]
  self._initial=digest('scheduler-config',(policy,self._bus._state_digest(self._bus._s),producer_id))
 def _authorize(self,actor,op):
  ident(actor);need((actor,op) in self.policy.grants,'AUTHORIZATION')
  self._bus.authority.authorize(actor,'inspect','admin')
 def _rows(self,state):
  tasks=tuple(FrozenJSON.make((k,v['request'].commitment,v['deps'],v['priority'],v['submitted'],v['deadline'],v['max_attempts'],v['attempts'],v['worker'],v['assignment'],v['until'],v['state'],v['outcome'],v['order'])) for k,v in sorted(state['tasks'].items()))
  workers=tuple(FrozenJSON.make((k,v['identity'].commitment,v['concurrency'],v['status'],v['order'],tuple(sorted(t for t,x in state['tasks'].items() if x['state']=='RUNNING' and x['worker']==k)))) for k,v in sorted(state['workers'].items()))
  return tasks,workers
 def _digest(self,state,bus):
  t,w=self._rows(state)
  return digest('scheduler-state',(self._initial,state['tick'],state['sequence'],collection_digest('scheduler-tasks',t),collection_digest('scheduler-workers',w),bus._state_digest(bus._s)))
 def checkpoint(self,actor):
  self._authorize(actor,'checkpoint');t,w=self._rows(self._state)
  cp=Snapshot(self._state['tick'],self._state['sequence'],t,w,self._bus._state_digest(self._bus._s),self._journal[-1].record_hash if self._journal else '0'*64,self._initial,'0'*64)
  return replace(cp,commitment=digest('scheduler-checkpoint',cp.body()))
 def _tickof(self,time):
  fmt='%Y-%m-%dT%H:%M:%S.%fZ';delta=(datetime.strptime(time,fmt)-datetime.strptime(self._bus.config.epoch,fmt)).total_seconds()
  need(delta.is_integer() and 0<=delta<=1000000,'DEADLINE');return int(delta)
 def _release(self,t,state,outcome):t.update(state=state,outcome=outcome,until=0)
 def _advance(self,s,tick,events):
  for k,t in sorted(s['tasks'].items()):
   if t['state'] in TERMINAL:continue
   if tick>=t['deadline']:self._release(t,'EXPIRED','DEADLINE');events.append(('TASK_FAILED',k));continue
   if t['state']=='RUNNING' and tick>=t['until']:
    self._release(t,'READY' if t['attempts']<t['max_attempts'] else 'FAILED','ASSIGNMENT_TIMEOUT');events.append(('TASK_FAILED',k))
  self._propagate(s,events);s['tick']=tick
 def _propagate(self,s,events):
  for _ in range(len(s['tasks'])+1):
   changed=False
   for k,t in sorted(s['tasks'].items()):
    if t['state'] in TERMINAL or t['state']=='RUNNING':continue
    deps=[s['tasks'][d]['state'] for d in t['deps']]
    bad=[d for d in deps if d in ('FAILED','CANCELLED','EXPIRED')]
    if bad:self._release(t,'CANCELLED' if 'CANCELLED' in bad else 'FAILED','DEPENDENCY_FAILED');events.append(('DEPENDENCIES_UPDATED',k));changed=True
    elif all(d=='SUCCEEDED' for d in deps) and t['state']=='WAITING':t['state']='READY';events.append(('TASK_QUEUED',k));changed=True
   if not changed:break
  need(sum(t['state']=='READY' for t in s['tasks'].values())<=self.policy.max_ready,'READY_CAPACITY')
 def _graph(self,s):
  pending=set(s['tasks']);done=set()
  while pending:
   ready=sorted(k for k in pending if set(s['tasks'][k]['deps'])<=done)
   need(bool(ready),'CYCLE');done.update(ready);pending.difference_update(ready)
 def _apply(self,s,op,actor,args,tick,events):
  if op=='recover':
   ident(args['task_id']);need(args['task_id'] in s['tasks'],'UNKNOWN_TASK');t=s['tasks'][args['task_id']]
   need(t['state']=='RUNNING','RECOVERY_STATE');need(t['assignment']==args['assignment_id'] and t['attempts']==args['attempt'],'STALE_ASSIGNMENT');need(tick<t['until'] and tick<t['deadline'],'STALE_ASSIGNMENT');need(args['mode'] in ('REQUEUE','RELEASE_LEASE'),'RECOVERY_POLICY')
  if op=='complete':
   ident(args['task_id']);need(args['task_id'] in s['tasks'],'UNKNOWN_TASK');t=s['tasks'][args['task_id']]
   need(type(args['success']) is bool,'OUTCOME');ident(args['assignment_id'])
   need(t['worker']==actor,'COMPLETION_OWNER');need(t['assignment']==args['assignment_id'],'STALE_ASSIGNMENT')
   identity=s['workers'][actor]['identity'];decision=self._bus.authority.policy.decide(actor,t['request'].capability_required,identity.capability_set);need(decision.decision=='ALLOW','AUTHORIZATION')
   if t['state'] in ('SUCCEEDED','FAILED') and t['outcome'] in ('SUCCESS','WORKER_FAILED'):
    need((t['outcome']=='SUCCESS')==args['success'],'TERMINAL');return 'DUPLICATE'
   need(t['state']=='RUNNING' and tick<t['until'] and tick<t['deadline'],'STALE_ASSIGNMENT')
  self._advance(s,tick,events)
  if op=='admit':
   rows=args['tasks'];need(type(rows) is list and 0<len(rows)<=16,'BATCH')
   need(len(s['tasks'])+len(rows)<=self.policy.max_tasks,'TASK_CAPACITY')
   ids=[]
   for row in rows:
    need(type(row) is dict and set(row)=={'request','dependencies','max_attempts'},'SCHEMA')
    raw=dict(row['request']);raw['payload']=FrozenJSON.make(raw['payload']);q=TaskRequest(**raw);check(q,TaskRequest)
    need(q.requester_id==actor,'AUTHORIZATION')
    identity=next((i for i in self._bus.authority.identities if i.worker_id==actor),None);need(identity is not None,'AUTHORIZATION')
    need(self._bus.authority.policy.decide(actor,q.capability_required,identity.capability_set).decision=='ALLOW','AUTHORIZATION')
    need(q.task_id not in s['tasks'] and q.task_id not in ids,'DUPLICATE_TASK');need(all(v['request'].idempotency_key!=q.idempotency_key for v in s['tasks'].values()),'DUPLICATE_TASK')
    deps=row['dependencies'];need(type(deps) is list and len(deps)<=16,'DEPENDENCIES')
    for d in deps:ident(d)
    need(len(set(deps))==len(deps),'DEPENDENCIES');nat(row['max_attempts'],1,5)
    deadline=self._tickof(q.deadline);need(self._tickof(q.created_at)<=tick<deadline,'DEADLINE')
    s['sequence']+=1;s['tasks'][q.task_id]=dict(request=q,deps=tuple(deps),priority=q.priority,submitted=tick,deadline=deadline,max_attempts=row['max_attempts'],attempts=0,worker=None,assignment=None,until=0,state='WAITING',outcome='',order=s['sequence']);ids.append(q.task_id)
    events.extend((('TASK_SUBMITTED',q.task_id),('TASK_VALIDATED',q.task_id)))
   for t in s['tasks'].values():need(set(t['deps'])<=set(s['tasks']),'UNKNOWN_DEPENDENCY');need(t['request'].parent_task_id is None or t['request'].parent_task_id in s['tasks'],'UNKNOWN_DEPENDENCY')
   self._graph(s);self._propagate(s,events)
  elif op=='register':
   raw=dict(args['identity']);raw['capability_set']=tuple(raw['capability_set']);raw['metadata']=FrozenJSON.make(raw['metadata']);identity=RuntimeIdentity(**raw);check(identity,RuntimeIdentity)
   need(identity.identity_type=='WORKER','WORKER_IDENTITY')
   pinned=next((i for i in self._bus.authority.identities if i.worker_id==identity.worker_id),None);need(pinned==identity,'WORKER_IDENTITY')
   need(identity.worker_id not in s['workers'],'DUPLICATE_WORKER');need(len(s['workers'])<self.policy.max_workers,'WORKER_CAPACITY');nat(args['max_concurrency'],1,16)
   s['workers'][identity.worker_id]=dict(identity=identity,concurrency=args['max_concurrency'],status='AVAILABLE',order=len(s['workers']));events.append(('WORKER_REGISTERED',identity.worker_id))
  elif op=='dispatch':
   nat(args['limit'],1,32);count=0
   ready=sorted((k for k,t in s['tasks'].items() if t['state']=='READY'),key=lambda k:(-(s['tasks'][k]['priority']+(tick-s['tasks'][k]['submitted'])//self.policy.aging_ticks),s['tasks'][k]['order'],k))
   if 'task_id' in args:
    need(args['task_id'] in ready,'TASK_INELIGIBLE');ready=[args['task_id']]
   for k in ready:
    if count>=args['limit'] or sum(t['state']=='RUNNING' for t in s['tasks'].values())>=self.policy.max_active:break
    t=s['tasks'][k]
    for wid,w in sorted(s['workers'].items(),key=lambda kv:(kv[1]['order'],kv[0])):
     if w['status']!='AVAILABLE':continue
     if sum(x['state']=='RUNNING' and x['worker']==wid for x in s['tasks'].values())>=w['concurrency']:continue
     if self._bus.authority.policy.decide(wid,t['request'].capability_required,w['identity'].capability_set).decision!='ALLOW':continue
     t['attempts']+=1;t.update(state='RUNNING',worker=wid,assignment='a:'+digest('scheduler-assignment',(k,t['attempts'],wid)),until=min(tick+self.policy.timeout_ticks,t['deadline']),outcome='');events.append(('TASK_ASSIGNED',k));count+=1;break
  elif op=='complete':
   t=s['tasks'][args['task_id']];success=args['success'];self._release(t,'SUCCEEDED' if success else ('READY' if t['attempts']<t['max_attempts'] else 'FAILED'),'SUCCESS' if success else 'WORKER_FAILED');events.append(('TASK_COMPLETED' if success else 'TASK_FAILED',args['task_id']));self._propagate(s,events);events.append(('DEPENDENCIES_UPDATED',args['task_id']))
  elif op=='recover':
   t=s['tasks'][args['task_id']];self._release(t,'CANCELLED' if args['mode']=='RELEASE_LEASE' else ('READY' if t['attempts']<t['max_attempts'] else 'FAILED'),'RECOVERY_RELEASE' if args['mode']=='RELEASE_LEASE' else 'WORKER_FAILED');events.append(('TASK_FAILED',args['task_id']));self._propagate(s,events)
  elif op=='cancel':
   ident(args['task_id']);need(args['task_id'] in s['tasks'],'UNKNOWN_TASK');t=s['tasks'][args['task_id']];need(t['state'] not in TERMINAL,'TERMINAL');self._release(t,'CANCELLED','CANCELLED');events.append(('TASK_FAILED',args['task_id']));self._propagate(s,events)
  elif op=='worker_state':
   ident(args['worker_id']);need(args['worker_id'] in s['workers'],'UNKNOWN_WORKER');need(args['status'] in ('AVAILABLE','UNAVAILABLE','DISABLED'),'WORKER_STATE');s['workers'][args['worker_id']]['status']=args['status'];events.append(('WORKER_STATE',args['worker_id']))
  return 'OK'
 def _run(self,op,actor,args,tick):
  self._authorize(actor,op);nat(tick);need(tick>=self._state['tick'],'CLOCK_ROLLBACK');need(len(self._journal)<self.policy.max_operations,'OPERATION_BUDGET')
  command=FrozenJSON.make(dict(op=op,actor=actor,args=args,tick=tick));s=deepcopy(self._state);bus=deepcopy(self._bus);events=[]
  result=self._apply(s,op,actor,args,tick,events)
  if result=='DUPLICATE':return
  # One transactional event batch maps lifecycle phases to existing envelope types.
  need(len(events)<=128,'EVENT_BOUND')
  phase='TASK_COMPLETED' if op=='complete' and args['success'] else ('TASK_FAILED' if op in ('cancel','complete') else 'TASK_ACCEPTED')
  msg=Message('scheduler:'+str(len(self._journal)),'scheduler-trace',None,None,self.producer_id,bus.config.bus_id,phase,FrozenJSON.make({'scheduler_schema':'sys003-v1','phases':events,'operation':op}),bus.config.at(tick),bus.config.at(tick+1))
  bus.publish(self.producer_id,TOPIC,msg,tick)
  root=self._digest(s,bus);entry=Entry(len(self._journal),command,root,self._journal[-1].record_hash if self._journal else '0'*64,'0'*64);entry=replace(entry,record_hash=digest('scheduler-journal',entry.body()))
  self._state=s;self._bus=bus;self._journal.append(entry)
 def admit(self,actor,tasks,tick):
  need(type(tasks) is tuple and len(tasks)<=16,'BATCH');rows=[]
  for q,deps,attempts in tasks:check(q,TaskRequest);need(type(deps) is tuple,'DEPENDENCIES');rows.append(dict(request=FrozenJSON(canonical(q)).value(),dependencies=list(deps),max_attempts=attempts))
  self._run('admit',actor,{'tasks':rows},tick)
 def register(self,actor,identity,max_concurrency,tick):check(identity,RuntimeIdentity);self._run('register',actor,{'identity':FrozenJSON(canonical(identity)).value(),'max_concurrency':max_concurrency},tick)
 def dispatch(self,actor,tick,limit=32):self._run('dispatch',actor,{'limit':limit},tick)
 def dispatch_task(self,actor,task_id,tick):
  ident(task_id);self._run('dispatch',actor,{'limit':1,'task_id':task_id},tick)
 def recover_assignment(self,actor,task_id,assignment_id,attempt,mode,tick):
  ident(assignment_id);nat(attempt,1,5);self._run('recover',actor,dict(task_id=task_id,assignment_id=assignment_id,attempt=attempt,mode=mode),tick)
 def complete(self,actor,task_id,assignment_id,success,tick):self._run('complete',actor,dict(task_id=task_id,assignment_id=assignment_id,success=success),tick)
 def cancel(self,actor,task_id,tick):self._run('cancel',actor,{'task_id':task_id},tick)
 def advance(self,actor,tick):self._run('advance',actor,{},tick)
 def worker_state(self,actor,worker_id,status,tick):self._run('worker_state',actor,dict(worker_id=worker_id,status=status),tick)
 def replay(self,actor,records):
  self._authorize(actor,'replay');need(type(records) is tuple and len(records)<=self.policy.max_operations,'REPLAY_LIMIT');out=Scheduler(self._seed,self.policy,self.producer_id)
  for i,e in enumerate(records):
   need(type(e) is Entry and e.sequence==i and e.previous_hash==(records[i-1].record_hash if i else '0'*64),'JOURNAL_TAMPERED');e.verify();v=e.command.value()
   out._run(v['op'],v['actor'],v['args'],v['tick']);need(out._journal[-1]==e,'REPLAY_DIVERGENCE')
  return out
