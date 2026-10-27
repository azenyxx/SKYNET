from fixtures import *
import time,json
class Tests(Base):
 def test_ten_producers_consumers(self):
  start=time.monotonic();actors=tuple('a'+str(i) for i in range(10))
  ids=tuple(RuntimeIdentity('runtime','node',a,T,('system.observe',),FrozenJSON.make({})) for a in actors)
  rights=tuple((a,op,Q if op in ('publish','subscribe','poll','ack') else 'admin') for a in actors for op in ('publish','subscribe','poll','ack','inspect','replay'))
  auth=Authority(HostPolicy('host',tuple((a,'system.observe') for a in actors)),ids,rights)
  b=Bus(Config(),(Topic(Q,('TASK_SUBMITTED',)),),auth)
  for a in actors:b.subscribe(a,Q,'s'+a,0)
  for a in actors:b.publish(a,Q,msg('m'+a,producer_id=a),0)
  peak=dict(b.inspect('a0',0).metrics)['queue_depth'];self.assertEqual(peak,100)
  for a in actors:
   for _ in actors:
    d=b.poll(a,'s'+a,0);b.ack(a,d.delivery_id,d.attempt_number,0)
  v=b.inspect('a0',0);rep=b.replay('a0',v.journal)
  self.assertEqual(rep._state_digest(rep._s),v.state_digest);self.assertEqual(dict(v.metrics)['acknowledged_total'],100)
  print('LOAD_RESULT '+json.dumps(dict(producers=10,consumers=10,published=10,deliveries=100,peak_queue=peak,journal_events=len(v.journal),replay_equal=True,seconds=time.monotonic()-start)))
 def test_single_producer_consumer(self):
  b,d=flight();b.ack('c',d.delivery_id,1,0);v=snap(b);self.assertEqual(dict(v.metrics)['acknowledged_total'],1);self.assertEqual(v.deliveries[0].message_digest,msg().commitment)
