from fixtures import *

class Tests(Base):
 def test_full(self):
  b,d=sent(queue_limit=1);self.bad('QUEUE_FULL',lambda:b.publish('p',Q,msg('m2'),0));self.assertEqual(snap(b).backpressure,'REJECTING')
 def test_atomic_fanout(self):
  b=ready(queue_limit=1);b.subscribe('x',Q,'s2',0);self.bad('QUEUE_FULL',lambda:b.publish('p',Q,msg(),0));self.assertEqual(dict(snap(b).metrics)['published_total'],0)
 def test_oversize(self):
  b=ready(message_limit=400);self.bad('MESSAGE_TOO_LARGE',lambda:b.publish('p',Q,msg(payload=FrozenJSON.make('x'*1000)),0))
 def test_subscription_bound(self):
  b=ready(subscription_limit=1);self.bad('SUBSCRIPTION_LIMIT',lambda:b.subscribe('x',Q,'s2',0))
 def test_history_bound(self):
  b,d=flight(history_limit=1);b.ack('c',d.delivery_id,1,0);self.bad('HISTORY_FULL',lambda:b.publish('p',Q,msg('m2'),0))
 def test_free_capacity(self):
  b,d=flight(queue_limit=1);b.ack('c',d.delivery_id,1,0);self.assertEqual(len(b.publish('p',Q,msg('m2'),0)),1)
 def test_config_bounds(self):
  self.bad('INVALID_SCHEMA',lambda:Config(queue_limit=0))
 def test_no_loss(self):
  b,d=sent(queue_limit=1);self.bad('QUEUE_FULL',lambda:b.publish('p',Q,msg('m2'),0));self.assertEqual(b.poll('c','s',0).message_id,'m')
