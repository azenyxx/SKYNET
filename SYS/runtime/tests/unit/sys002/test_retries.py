from fixtures import *

class Tests(Base):
 def test_delay(self):
  b,d=flight();b.nack('c',d.delivery_id,1,'TRANSIENT',0);self.assertIsNone(b.poll('c','s',1));self.assertEqual(b.poll('c','s',2).attempt_number,2)
 def test_visibility(self):
  b,d=flight();b.advance('admin',5);self.assertEqual(snap(b,5).deliveries[0].delivery_status,'RETRY_PENDING')
 def test_max_attempts(self):
  b,d=flight(retry=RetryPolicy(1,0,1));b.nack('c',d.delivery_id,1,'TRANSIENT',0);self.assertIsNone(b.poll('c','s',0))
 def test_expiry_no_retry(self):
  b=ready();b.publish('p',Q,msg(expires_at='2026-10-25T00:00:01.000000Z'),0);d=b.poll('c','s',0);b.advance('admin',1);self.assertEqual(snap(b,1).deliveries[0].delivery_status,'EXPIRED')
 def test_late_ack(self):
  b,d=flight();self.bad('INVALID_TRANSITION',lambda:b.ack('c',d.delivery_id,1,5))
 def test_clock(self):
  b=ready();b.advance('admin',3);self.bad('CLOCK_ROLLBACK',lambda:b.poll('c','s',2))
 def test_digest_stable(self):
  b,d=flight();b.nack('c',d.delivery_id,1,'TRANSIENT',0);d2=b.poll('c','s',2);self.assertEqual((d.message_digest,d.delivery_id),(d2.message_digest,d2.delivery_id))
 def test_zero_delay(self):
  b,d=flight(retry=RetryPolicy(2,0,5));b.nack('c',d.delivery_id,1,'TRANSIENT',0);self.assertEqual(b.poll('c','s',0).attempt_number,2)
