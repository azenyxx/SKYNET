from fixtures import *

class Tests(Base):
 def test_exhaustion(self):
  b,d=flight(retry=RetryPolicy(1,0,1));b.nack('c',d.delivery_id,1,'REJECTED',0);v=snap(b);self.assertEqual(v.dead_letters[0].attempt_count,1)
 def test_reason(self):
  b,d=flight(retry=RetryPolicy(1,0,1));b.advance('admin',1);self.assertEqual(snap(b,1).dead_letters[0].failure_reason,'VISIBILITY_TIMEOUT')
 def test_capacity_no_loss(self):
  b,d=flight(retry=RetryPolicy(1,0,5),dead_letter_limit=1);b.nack('c',d.delivery_id,1,'REJECTED',0);b.publish('p',Q,msg('m2'),0);d2=b.poll('c','s',0);self.bad('DLQ_FULL',lambda:b.nack('c',d2.delivery_id,1,'REJECTED',0));self.assertEqual(b._s['deliveries'][d2.delivery_id].delivery_status,'IN_FLIGHT')
 def test_immutable_terminal(self):
  b,d=flight(retry=RetryPolicy(1,0,5));b.nack('c',d.delivery_id,1,'REJECTED',0);self.bad('INVALID_TRANSITION',lambda:b.ack('c',d.delivery_id,1,0))
 def test_replay(self):
  b,d=flight(retry=RetryPolicy(1,0,5));b.nack('c',d.delivery_id,1,'REJECTED',0);v=snap(b);self.assertEqual(b.replay('admin',v.journal)._s['dlq'],b._s['dlq'])
 def test_no_auto_redelivery(self):
  b,d=flight(retry=RetryPolicy(1,0,5));b.nack('c',d.delivery_id,1,'REJECTED',0);self.assertIsNone(b.poll('c','s',10))
