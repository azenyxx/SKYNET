import unittest
from dataclasses import replace
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.capabilities import HostPolicy
from skynet_sys.canonical import FrozenJSON,digest
from skynet_sys.messages import Message
from skynet_sys.errors import ContractError
from skynet_sys_transport.contracts import *
from skynet_sys_transport.authorization import Authority
from skynet_sys_transport.bus import Bus
from skynet_sys_transport.journal import verify_chain
T='2026-10-25T00:00:00.000000Z'
Q='cognitive.tasks'
def msg(i='m',**kw):
 d=dict(message_id=i,trace_id='trace',correlation_id=None,causation_id=None,producer_id='p',recipient_id='bus',message_type='TASK_SUBMITTED',payload=FrozenJSON.make({'x':1}),created_at=T,expires_at='2026-10-25T01:00:00.000000Z');d.update(kw);return Message(**d)
def fixture(**kw):
 config=Config(**kw);ids=tuple(RuntimeIdentity('runtime','node',a,T,('system.observe',),FrozenJSON.make({})) for a in ('p','c','x','admin'))
 rights=tuple((a,op,scope) for a in ('p','c','x','admin') for op in OPS for scope in ((Q,'agent.events') if op in ('publish','subscribe','unsubscribe','poll','ack','nack') else ('admin',)))
 auth=Authority(HostPolicy('host',tuple((a,'system.observe') for a in ('p','c','x','admin'))),ids,rights)
 return Bus(config,(Topic(Q,('TASK_SUBMITTED',)),Topic('agent.events',('WORKER_HEARTBEAT',))),auth)
def ready(**kw):
 b=fixture(**kw);b.subscribe('c',Q,'s',0);return b
def sent(**kw):
 b=ready(**kw);d=b.publish('p',Q,msg(),0)[0];return b,d
def flight(**kw):
 b,_=sent(**kw);return b,b.poll('c','s',0)
def snap(b,tick=0):return b.inspect('admin',tick)
class Base(unittest.TestCase):
 def bad(self,code,f):
  with self.assertRaisesRegex((BusError,ContractError),'^'+code+'$'):f()
