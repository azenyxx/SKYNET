import unittest,time,json
from dataclasses import replace
from copy import deepcopy
from skynet_sys.canonical import FrozenJSON
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.capabilities import HostPolicy
from skynet_sys.tasks import TaskRequest
from skynet_sys.errors import ContractError
from skynet_sys_transport.contracts import Config,Topic,BusError
from skynet_sys_transport.authorization import Authority
from skynet_sys_transport.bus import Bus
from skynet_sys_scheduler.contracts import *
from skynet_sys_scheduler.scheduler import Scheduler,TOPIC
T='2026-10-25T00:00:00.000000Z'
def identw(a):return RuntimeIdentity('runtime','node',a,T,('system.observe',) if a.startswith('w') else ('system.observe','cognitive.reason'),FrozenJSON.make({}))
def task(k='t',priority=0,cap='system.observe',deadline='2026-10-25T01:00:00.000000Z'):
 return TaskRequest(k,None,'trace','p',cap,FrozenJSON.make({}),priority,deadline,'key:'+k,T)
def fixture(queue=1024,**kw):
 actors=('p','admin','c')+tuple('w'+str(i) for i in range(10));ids=tuple(identw(a) for a in actors)
 grants=tuple((a,c) for a in actors for c in identw(a).capability_set)
 rights=tuple((a,'inspect','admin') for a in actors)+(('p','publish',TOPIC),('c','subscribe',TOPIC))
 b=Bus(Config(queue_limit=queue,journal_limit=2048,history_limit=1024),(Topic(TOPIC,('TASK_ACCEPTED','TASK_COMPLETED','TASK_FAILED')),),Authority(HostPolicy('p',grants),ids,rights));b.subscribe('c',TOPIC,'sub',0)
 p=Policy(tuple((a,op) for a in actors for op in (('complete',) if a.startswith('w') else OPS)),**kw)
 return Scheduler(b,p)
def ready(**kw):
 s=fixture(**kw);s.register('admin',identw('w0'),1,0);return s
def add(s,k='t',deps=(),priority=0,attempts=1,tick=0,**kw):s.admit('p',((task(k,priority,**kw),deps,attempts),),tick)
def finish(s,k='t',success=True,tick=0):
 t=s._state['tasks'][k];s.complete(t['worker'],k,t['assignment'],success,tick)
class Tests(unittest.TestCase):
 def bad(self,code,f):
  with self.assertRaisesRegex((SchedulingError,ContractError,BusError),'^'+code+'$'):f()
 def test_admission_valid(self):
  s=ready();add(s);self.assertEqual(s._state['tasks']['t']['state'],'READY')
 def test_admission_denied(self):
  s=ready();self.bad('AUTHORIZATION',lambda:s.admit('evil',((task(),(),1),),0))
 def test_admission_duplicate(self):
  s=ready();add(s);before=deepcopy(s._state);self.bad('DUPLICATE_TASK',lambda:add(s));self.assertEqual(s._state,before)
 def test_admission_capacity(self):
  s=ready(max_tasks=1);add(s);self.bad('TASK_CAPACITY',lambda:add(s,'other'))
 def test_admission_version(self):
  self.bad('UNSUPPORTED_VERSION',lambda:replace(task(),schema_version='bad'))
 def test_admission_deadline(self):
  s=ready();self.bad('DEADLINE',lambda:add(s,tick=3600))
 def test_admission_unknown_dependency(self):
  s=ready();self.bad('UNKNOWN_DEPENDENCY',lambda:add(s,deps=('missing',)));self.assertFalse(s._state['tasks'])
 def test_graphs_cycle(self):
  s=ready();self.bad('CYCLE',lambda:s.admit('p',((task('a'),('b',),1),(task('b'),('a',),1)),0));self.assertFalse(s._state['tasks'])
 def test_graphs_self_cycle(self):
  s=ready();self.bad('CYCLE',lambda:add(s,deps=('t',)))
 def test_graphs_waiting(self):
  s=ready();add(s,'a');add(s,'b',('a',));s.dispatch('admin',0);self.assertEqual(s._state['tasks']['b']['state'],'WAITING')
 def test_graphs_success_unlock(self):
  s=ready();add(s,'a');add(s,'b',('a',));s.dispatch('admin',0);finish(s,'a');self.assertEqual(s._state['tasks']['b']['state'],'READY')
 def test_graphs_failure(self):
  s=ready();add(s,'a');add(s,'b',('a',));s.dispatch('admin',0);finish(s,'a',False);self.assertEqual(s._state['tasks']['b']['state'],'FAILED')
 def test_graphs_cancel_propagation(self):
  s=ready();add(s,'a');add(s,'b',('a',));s.cancel('admin','a',0);self.assertEqual(s._state['tasks']['b']['state'],'CANCELLED')
 def test_graphs_four_levels(self):
  s=ready();
  for i in range(4):add(s,'t'+str(i),('t'+str(i-1),) if i else ())
  for i in range(4):s.dispatch('admin',0);finish(s,'t'+str(i))
  self.assertTrue(all(t['state']=='SUCCEEDED' for t in s._state['tasks'].values()))
 def test_graphs_batch_forward_refs(self):
  s=ready();s.admit('p',((task('b'),('a',),1),(task('a'),(),1)),0);self.assertEqual(s._state['tasks']['b']['state'],'WAITING')
 def test_workers_registration(self):
  s=ready();self.assertEqual(s._state['workers']['w0']['status'],'AVAILABLE')
 def test_workers_duplicate(self):
  s=ready();self.bad('DUPLICATE_WORKER',lambda:s.register('admin',identw('w0'),1,0))
 def test_workers_mismatch(self):
  s=ready();add(s,cap='cognitive.reason');s.dispatch('admin',0);self.assertEqual(s._state['tasks']['t']['state'],'READY')
 def test_workers_unknown_cap(self):
  self.bad('CAPABILITY_DENIED',lambda:replace(identw('w0'),capability_set=('root',)))
 def test_workers_forged_identity(self):
  s=fixture();self.bad('WORKER_IDENTITY',lambda:s.register('admin',replace(identw('w0'),node_id='other'),1,0))
 def test_workers_unavailable(self):
  s=ready();s.worker_state('admin','w0','UNAVAILABLE',0);add(s);s.dispatch('admin',0);self.assertEqual(s._state['tasks']['t']['state'],'READY')
 def test_dispatch_priority(self):
  s=ready();add(s,'low',priority=0);add(s,'high',priority=100);s.dispatch('admin',0);self.assertEqual(s._state['tasks']['high']['state'],'RUNNING')
 def test_dispatch_tie(self):
  s=ready();add(s,'z');add(s,'a');s.dispatch('admin',0);self.assertEqual(s._state['tasks']['z']['state'],'RUNNING')
 def test_dispatch_concurrency(self):
  s=ready();add(s,'a');add(s,'b');s.dispatch('admin',0);self.assertEqual(sum(t['state']=='RUNNING' for t in s._state['tasks'].values()),1)
 def test_dispatch_aging(self):
  s=ready();add(s,'low');
  for i in range(3):
   add(s,'high'+str(i),priority=100,tick=i);s.dispatch('admin',i);finish(s,'high'+str(i),tick=i)
  add(s,'fresh',priority=100,tick=101);s.dispatch('admin',101);self.assertEqual(s._state['tasks']['low']['state'],'RUNNING')
 def test_dispatch_stable_worker(self):
  s=ready();s.register('admin',identw('w1'),1,0);add(s);s.dispatch('admin',0);self.assertEqual(s._state['tasks']['t']['worker'],'w0')
 def test_dispatch_active_limit(self):
  s=fixture(max_active=1);s.register('admin',identw('w0'),2,0);add(s,'a');add(s,'b');s.dispatch('admin',0);self.assertEqual(sum(t['state']=='RUNNING' for t in s._state['tasks'].values()),1)
 def test_dispatch_ready_limit(self):
  s=ready(max_ready=1);add(s);self.bad('READY_CAPACITY',lambda:add(s,'b'));self.assertNotIn('b',s._state['tasks'])
 def test_dispatch_clock(self):
  s=ready();s.advance('admin',1);self.bad('CLOCK_ROLLBACK',lambda:s.dispatch('admin',0))
 def test_parallel_two_active(self):
  s=fixture();s.register('admin',identw('w0'),2,0);add(s,'a');add(s,'b');s.dispatch('admin',0);self.assertEqual(sum(t['state']=='RUNNING' for t in s._state['tasks'].values()),2)
 def test_parallel_join(self):
  s=fixture();s.register('admin',identw('w0'),2,0);add(s,'a');add(s,'b');add(s,'join',('a','b'));s.dispatch('admin',0);finish(s,'a');self.assertEqual(s._state['tasks']['join']['state'],'WAITING');finish(s,'b');self.assertEqual(s._state['tasks']['join']['state'],'READY')
 def test_parallel_independent(self):
  s=fixture();s.register('admin',identw('w0'),2,0);add(s,'a');add(s,'b');s.dispatch('admin',0);finish(s,'a',False);self.assertEqual(s._state['tasks']['b']['state'],'RUNNING')
 def test_parallel_cancel_active(self):
  s=ready();add(s);s.dispatch('admin',0);s.cancel('admin','t',0);self.assertEqual(s._state['tasks']['t']['state'],'CANCELLED')
 def test_parallel_no_double_assignment(self):
  s=ready();add(s);s.dispatch('admin',0);a=s._state['tasks']['t']['assignment'];s.dispatch('admin',0);self.assertEqual(s._state['tasks']['t']['assignment'],a)
 def test_failures_timeout(self):
  s=ready();add(s);s.dispatch('admin',0);s.advance('admin',10);self.assertEqual(s._state['tasks']['t']['state'],'FAILED')
 def test_failures_retry(self):
  s=ready();add(s,attempts=2);s.dispatch('admin',0);old=s._state['tasks']['t']['assignment'];s.advance('admin',10);s.dispatch('admin',10);self.assertNotEqual(s._state['tasks']['t']['assignment'],old);self.bad('STALE_ASSIGNMENT',lambda:s.complete('w0','t',old,True,10))
 def test_failures_duplicate_complete(self):
  s=ready();add(s);s.dispatch('admin',0);a=s._state['tasks']['t']['assignment'];finish(s);n=len(s._journal);s.complete('w0','t',a,True,0);self.assertEqual(len(s._journal),n)
 def test_failures_wrong_owner(self):
  s=ready();add(s);s.dispatch('admin',0);a=s._state['tasks']['t']['assignment'];self.bad('COMPLETION_OWNER',lambda:s.complete('w1','t',a,True,0))
 def test_failures_expiry(self):
  s=ready();add(s,deadline='2026-10-25T00:00:01.000000Z');s.advance('admin',1);self.assertEqual(s._state['tasks']['t']['state'],'EXPIRED')
 def test_failures_terminal(self):
  s=ready();add(s);s.dispatch('admin',0);finish(s);self.bad('TERMINAL',lambda:s.cancel('admin','t',0))
 def test_replay_equality(self):
  s=ready();add(s);s.dispatch('admin',0);finish(s);o=s.replay('admin',tuple(s._journal));self.assertEqual(s.checkpoint('admin'),o.checkpoint('admin'))
 def test_replay_checkpoint(self):
  s=ready();add(s);cp=s.checkpoint('admin');cp.verify();self.bad('CHECKPOINT_TAMPERED',lambda:replace(cp,logical_tick=1).verify())
 def test_replay_journal_tamper(self):
  s=ready();e=replace(s._journal[0],record_hash='a'*64);self.bad('JOURNAL_TAMPERED',lambda:s.replay('admin',(e,)))
 def test_replay_determinism(self):
  a=ready();b=ready();add(a);add(b);a.dispatch('admin',0);b.dispatch('admin',0);self.assertEqual(a.checkpoint('admin'),b.checkpoint('admin'))
 def test_replay_replay_denied(self):
  s=ready();self.bad('AUTHORIZATION',lambda:s.replay('evil',tuple(s._journal)))
 def test_integration_real_envelope(self):
  s=ready();add(s);self.assertEqual(s._bus._s['metrics']['published_total'],2)
 def test_integration_backpressure_atomic(self):
  s=ready(queue=1);before=deepcopy(s._state);head=s._bus._journal[-1];self.bad('QUEUE_FULL',lambda:add(s));self.assertEqual(s._state,before);self.assertEqual(s._bus._journal[-1],head)
 def test_integration_schema_mapping(self):
  s=ready();add(s);messages=[v[1] for v in s._bus._s['messages'].values()];self.assertTrue(all(m.message_type=='TASK_ACCEPTED' for m in messages));self.assertIn('TASK_VALIDATED',str(messages[-1].payload.value()))
 def test_integration_bus_policy(self):
  s=ready();s._bus.authority=replace(s._bus.authority,rights=tuple(x for x in s._bus.authority.rights if x[1]!='publish'));self.bad('CAPABILITY_DENIED',lambda:add(s));self.assertFalse(s._state['tasks'])
 def test_integration_task_unchanged(self):
  s=ready();q=task();h=q.commitment;s.admit('p',((q,(),1),),0);s.dispatch('admin',0);self.assertEqual(q.commitment,h)
 def test_load_100_tasks_10_workers(self):
  start=time.monotonic();s=fixture(max_active=64,timeout_ticks=1000)
  for i in range(10):s.register('admin',identw('w'+str(i)),10,0)
  for i in range(100):add(s,'load'+str(i))
  for _ in range(2):s.dispatch('admin',0)
  self.assertEqual(sum(t['state']=='RUNNING' for t in s._state['tasks'].values()),64)
  for k,t in list(s._state['tasks'].items()):
   if t['state']=='RUNNING':finish(s,k)
  for _ in range(2):s.dispatch('admin',0)
  for k,t in list(s._state['tasks'].items()):
   if t['state']=='RUNNING':finish(s,k)
  self.assertTrue(all(t['state']=='SUCCEEDED' for t in s._state['tasks'].values()))
  out=s.replay('admin',tuple(s._journal));self.assertEqual(s.checkpoint('admin'),out.checkpoint('admin'))
  print('LOAD_RESULT '+json.dumps(dict(tasks=100,workers=10,peak_assignments=64,journal_events=len(s._journal),digest_equal=True,seconds=time.monotonic()-start)))
