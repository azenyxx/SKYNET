from fixtures import *

class Tests(Base):
 def test_duplicate_publish(self):
  b,d=sent();self.bad('DUPLICATE_MESSAGE',lambda:b.publish('p',Q,msg(),0))
 def test_conflict(self):
  b,d=sent();self.bad('IDENTITY_CONFLICT',lambda:b.publish('p',Q,msg(payload=FrozenJSON.make('changed')),0))
 def test_terminal_retained(self):
  b,d=flight();b.ack('c',d.delivery_id,1,0);self.bad('DUPLICATE_MESSAGE',lambda:b.publish('p',Q,msg(),0))
 def test_sub_identity(self):
  b=ready();b.unsubscribe('c','s',0);self.bad('DUPLICATE_MESSAGE',lambda:b.subscribe('x',Q,'s',0))
 def test_delivery_identity(self):
  b=ready();b.subscribe('x',Q,'s2',0);ds=b.publish('p',Q,msg(),0);self.assertNotEqual(ds[0].delivery_id,ds[1].delivery_id)
 def test_retry_same_message(self):
  b,d=flight();b.nack('c',d.delivery_id,1,'TRANSIENT',0);b.poll('c','s',2);self.assertEqual(dict(snap(b,2).metrics)['published_total'],1)
 def test_duplicate_metrics(self):
  b,d=sent();self.bad('DUPLICATE_MESSAGE',lambda:b.publish('p',Q,msg(),0));self.assertEqual(dict(snap(b).metrics)['duplicate_total'],1)
 def test_retry_fifo(self):
  b,d=flight();b.publish('p',Q,msg('later'),0);b.nack('c',d.delivery_id,1,'TRANSIENT',0);self.assertIsNone(b.poll('c','s',1));self.assertEqual(b.poll('c','s',2).message_id,'m')
