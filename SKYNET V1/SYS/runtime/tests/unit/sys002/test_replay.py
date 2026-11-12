from fixtures import *

class Tests(Base):
 def test_state(self):
  b,d=flight();view=snap(b);rep=b.replay('admin',view.journal);self.assertEqual(rep._state_digest(rep._s),view.state_digest)
 def test_metrics(self):
  b,d=flight();b.nack('c',d.delivery_id,1,'TRANSIENT',0);v=snap(b);rep=b.replay('admin',v.journal);self.assertEqual(rep._s['metrics'],b._s['metrics'])
 def test_denied_command(self):
  b=ready();self.bad('CAPABILITY_DENIED',lambda:b.publish('evil',Q,msg(),0));v=snap(b);self.assertEqual(b.replay('admin',v.journal)._s,b._s)
 def test_wrong_config(self):
  b=ready();v=snap(b);other=ready(queue_limit=1);self.bad('REPLAY_DIVERGENCE',lambda:other.replay('admin',v.journal))
 def test_limit(self):
  b=ready(replay_limit=1);v=snap(b);self.bad('REPLAY_LIMIT',lambda:b.replay('admin',v.journal))
 def test_closed(self):
  b=ready();b.close('admin',0);v=snap(b);self.assertTrue(b.replay('admin',v.journal)._s['closed'])
 def test_rejection_state(self):
  b,d=sent(queue_limit=1);self.bad('QUEUE_FULL',lambda:b.publish('p',Q,msg('m2'),0));v=snap(b);self.assertEqual(b.replay('admin',v.journal)._s,b._s)
 def test_thousand_events(self):
  import time,json
  start=time.monotonic();b=ready();
  for _ in range(1000):b.advance('admin',0)
  v=snap(b);rep=b.replay('admin',v.journal);self.assertEqual(len(rep._journal),1002);self.assertEqual(rep._state_digest(rep._s),v.state_digest);print('REPLAY_LOAD_RESULT '+json.dumps(dict(events=1002,replay_equal=True,seconds=time.monotonic()-start)))
 def test_replay_authorization_audited(self):
  b=ready();v=snap(b);b.replay('admin',v.journal)
  self.assertEqual(b._journal[-1].event_type,'replay');self.assertEqual(b._journal[-1].authorization_decision,'ALLOW')
 def test_malformed_command_shape(self):
  b=ready();n=len(b._journal)
  self.bad('INVALID_SCHEMA',lambda:b._execute('publish','p',0,{}));self.assertEqual(len(b._journal),n)
 def test_replay_authorization_record_replays_without_recursion(self):
  b=ready();v=snap(b);b.replay('admin',v.journal);v2=snap(b)
  out=b.replay('admin',v2.journal);self.assertEqual(out._state_digest(out._s),v2.state_digest)

 def test_closed_replay_unauthorized_state_immutable(self):
  from copy import deepcopy
  b=ready();b.close('admin',0);v=snap(b);before=deepcopy(b._s)
  self.bad('CAPABILITY_DENIED',lambda:b.replay('evil',v.journal))
  self.assertEqual(b._s,before);self.assertEqual(b._journal[-1].authorization_decision,'DENY')
 def test_closed_tampered_replay_rejected(self):
  from copy import deepcopy
  b=ready();b.close('admin',0);v=snap(b);before=deepcopy(b._s)
  forged=(replace(v.journal[0],record_hash='a'*64),)+v.journal[1:]
  self.bad('JOURNAL_TAMPERED',lambda:b.replay('admin',forged))
  self.assertEqual(b._s,before)
 def test_closed_replay_preserves_source_and_digest(self):
  from copy import deepcopy
  b,d=flight();b.close('admin',0);v=snap(b);before=deepcopy(b._s);n=len(v.journal)
  out=b.replay('admin',v.journal)
  self.assertEqual(b._s,before);self.assertTrue(out._s['closed'])
  self.assertEqual(out._state_digest(out._s),v.state_digest)
  self.assertEqual(b._state_digest(b._s),v.state_digest);self.assertEqual(len(b._journal),n+1)
 def test_closed_guard_preserved_after_replay(self):
  b,d=flight();b.close('admin',0);v=snap(b);b.replay('admin',v.journal)
  self.bad('CLOSED',lambda:b.publish('p',Q,msg('other'),0))
  self.bad('CLOSED',lambda:b.ack('c',d.delivery_id,1,0))
  self.bad('CLOSED',lambda:b.nack('c',d.delivery_id,1,'TRANSIENT',0))
  self.assertEqual(b._s['deliveries'][d.delivery_id],d);self.assertTrue(b._s['closed'])
 def test_replay_still_requires_sys001_grant(self):
  from copy import deepcopy
  b=ready();v=snap(b)
  authority=replace(b.authority,policy=HostPolicy('deny',()))
  denied=Bus(b.config,b.topics,authority);before=deepcopy(denied._s)
  self.bad('CAPABILITY_DENIED',lambda:denied.replay('admin',v.journal))
  self.assertEqual(denied._s,before)
 def test_closed_replay_deterministic_repeated(self):
  b=ready();b.close('admin',0);v=snap(b)
  a=b.replay('admin',v.journal);c=b.replay('admin',v.journal)
  self.assertEqual(a._s,c._s);self.assertEqual(a._journal,c._journal)
