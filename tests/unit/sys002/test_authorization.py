from fixtures import *

class Tests(Base):
 def test_unauthorized_publish(self):
  b=ready();self.bad('CAPABILITY_DENIED',lambda:b.publish('evil',Q,msg(producer_id='evil'),0))
 def test_unauthorized_subscribe(self):
  self.bad('CAPABILITY_DENIED',lambda:fixture().subscribe('evil',Q,'s',0))
 def test_unauthorized_inspect(self):
  self.bad('CAPABILITY_DENIED',lambda:fixture().inspect('evil',0))
 def test_unauthorized_replay(self):
  self.bad('CAPABILITY_DENIED',lambda:fixture().replay('evil',()))
 def test_default_deny(self):
  b=fixture();a=replace(b.authority,rights=());q=Bus(b.config,b.topics,a);self.bad('CAPABILITY_DENIED',lambda:q.subscribe('c',Q,'s',0))
 def test_sys001_version(self):
  self.bad('UNSUPPORTED_VERSION',lambda:msg(schema_version='bad'))
 def test_sys001_payload(self):
  self.bad('INVALID_SCHEMA',lambda:msg(payload={}))
 def test_claimed_producer(self):
  b=ready();self.bad('CAPABILITY_DENIED',lambda:b.publish('x',Q,msg(),0))
