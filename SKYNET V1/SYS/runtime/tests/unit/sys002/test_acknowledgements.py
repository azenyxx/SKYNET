from fixtures import *

class Tests(Base):
 def test_ack(self):
  b,d=flight();self.assertEqual(b.ack('c',d.delivery_id,1,0).delivery_status,'ACKNOWLEDGED')
 def test_wrong_ack(self):
  b,d=flight();self.bad('WRONG_CONSUMER',lambda:b.ack('x',d.delivery_id,1,0))
 def test_before_poll(self):
  b,d=sent();self.bad('INVALID_TRANSITION',lambda:b.ack('c',d.delivery_id,1,0))
 def test_duplicate_ack(self):
  b,d=flight();b.ack('c',d.delivery_id,1,0);before=tuple(b._journal);b.ack('c',d.delivery_id,1,0);self.assertEqual(tuple(b._journal),before)
 def test_nack(self):
  b,d=flight();self.assertEqual(b.nack('c',d.delivery_id,1,'TRANSIENT',0).delivery_status,'RETRY_PENDING')
 def test_wrong_nack(self):
  b,d=flight();self.bad('WRONG_CONSUMER',lambda:b.nack('x',d.delivery_id,1,'TRANSIENT',0))
 def test_stale_attempt(self):
  b,d=flight();b.nack('c',d.delivery_id,1,'TRANSIENT',0);b.poll('c','s',2);self.bad('STALE_ATTEMPT',lambda:b.ack('c',d.delivery_id,1,2))
 def test_nack_terminal(self):
  b,d=flight();b.ack('c',d.delivery_id,1,0);self.bad('INVALID_TRANSITION',lambda:b.nack('c',d.delivery_id,1,'TRANSIENT',0))
