from fixtures import *

class Tests(Base):
 def test_exact(self):
  b=ready();b.subscribe('x','agent.events','other',0);ds=b.publish('p',Q,msg(),0);self.assertEqual([d.subscription_id for d in ds],['s'])
 def test_unknown(self):
  b=ready();self.bad('UNKNOWN_TOPIC',lambda:b.publish('p','unknown.topic',msg(),0))
 def test_wildcard(self):
  self.bad('UNKNOWN_TOPIC',lambda:Topic('cognitive.*',('TASK_SUBMITTED',)))
 def test_stable_fanout(self):
  b=ready();b.subscribe('x',Q,'a',0);ds=b.publish('p',Q,msg(),0);self.assertEqual([d.subscription_id for d in ds],['a','s'])
 def test_duplicate_sub(self):
  b=ready();self.bad('DUPLICATE_MESSAGE',lambda:b.subscribe('c',Q,'s',0))
 def test_unsub(self):
  b=ready();b.unsubscribe('c','s',0);self.bad('NO_SUBSCRIBERS',lambda:b.publish('p',Q,msg(),0))
 def test_busy_unsub(self):
  b,d=sent();self.bad('BUSY',lambda:b.unsubscribe('c','s',0));self.assertEqual(dict(snap(b).metrics)['queue_depth'],1)
 def test_typed_topic(self):
  b=ready();self.bad('INVALID_SCHEMA',lambda:b.publish('p',Q,msg(message_type='TASK_FAILED'),0))
