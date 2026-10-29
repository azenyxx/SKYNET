from fixtures import *

class Tests(Base):
 def test_available(self):
  b,d=sent();self.assertEqual(d.delivery_status,'AVAILABLE')
 def test_inflight(self):
  b,d=flight();self.assertEqual((d.delivery_status,d.attempt_number),('IN_FLIGHT',1))
 def test_fifo(self):
  b=ready();b.publish('p',Q,msg('a'),0);b.publish('p',Q,msg('b'),0);d=b.poll('c','s',0);self.assertEqual(d.message_id,'a');b.ack('c',d.delivery_id,1,0);self.assertEqual(b.poll('c','s',0).message_id,'b')
 def test_empty(self):
  self.assertIsNone(ready().poll('c','s',0))
 def test_no_parallel_same_delivery(self):
  b,d=flight();self.assertIsNone(b.poll('c','s',0))
 def test_terminal_no_reactivate(self):
  self.bad('INVALID_TRANSITION',lambda:transition('ACKNOWLEDGED','AVAILABLE'))
 def test_pending_transition(self):
  transition('PENDING','AVAILABLE');self.bad('INVALID_TRANSITION',lambda:transition('PENDING','ACKNOWLEDGED'))
 def test_expired(self):
  b=ready();b.publish('p',Q,msg(expires_at='2026-10-25T00:00:01.000000Z'),0);self.assertIsNone(b.poll('c','s',1));self.assertEqual(dict(snap(b,1).metrics)['expired_total'],1)
 def test_closed(self):
  b=ready();b.close('admin',0);self.bad('CLOSED',lambda:b.poll('c','s',0))
 def test_ownership_poll(self):
  b=ready();self.bad('WRONG_CONSUMER',lambda:b.poll('x','s',0))
