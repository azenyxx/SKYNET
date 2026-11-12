import unittest
from dataclasses import replace, FrozenInstanceError
from skynet_sys.canonical import *
from skynet_sys.errors import ContractError
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.capabilities import *
from skynet_sys.tasks import *
from skynet_sys.messages import Message
from skynet_sys.checkpoints import Checkpoint
from skynet_sys.evidence import EvidenceReference
from skynet_sys.runtime import Runtime
T='2026-10-25T00:00:00.000000Z'
L='2026-10-25T00:01:00.000000Z'
P=FrozenJSON.make({'text':'diagnostic'})
def identity(kind='WORKER',**kw):
    d=dict(runtime_id='runtime',node_id='node',worker_id='worker',created_at=T,capability_set=('system.observe',),metadata=FrozenJSON.make({}),identity_type=kind);d.update(kw);return RuntimeIdentity(**d)
def request(**kw):
    d=dict(task_id='task',parent_task_id=None,trace_id='trace',requester_id='worker',capability_required='system.observe',payload=P,priority=1,deadline=L,idempotency_key='key',created_at=T);d.update(kw);return TaskRequest(**d)
def message(**kw):
    d=dict(message_id='message',trace_id='trace',correlation_id=None,causation_id=None,producer_id='worker',recipient_id='runtime',message_type='WORKER_HEARTBEAT',payload=P,created_at=T,expires_at=L);d.update(kw);return Message(**d)
def runtime(grant=True):
    rt=Runtime('runtime',HostPolicy('policy',(('worker','system.observe'),) if grant else ()));rt.register_node(identity('NODE'),T);rt.register_worker(identity(),T);return rt
def evidence(**kw):
    d=dict(evidence_id='ev',producer_id='worker',subject_id='task',artifact_digest='a'*64,artifact_type='diagnostic',created_at=T,verification_status='UNVERIFIED');d.update(kw);return EvidenceReference(**d)
class Tests(unittest.TestCase):
    def reject(self,code,fn):
        with self.assertRaisesRegex(ContractError,'^'+code+'$'):fn()
    def test_valid(self):
        message().validate_at(T)
    def test_unknown(self):
        self.reject('INVALID_SCHEMA',lambda:message(message_type='EXEC_SHELL'))
    def test_expiry(self):
        self.reject('EXPIRED_MESSAGE',lambda:message().validate_at(L))
    def test_future(self):
        self.reject('EXPIRED_MESSAGE',lambda:message(created_at=L,expires_at='2026-10-25T00:02:00.000000Z').validate_at(T))
    def test_duplicate(self):
        rt=runtime();rt.accept_message(message(),T);n=len(rt.audit);self.reject('DUPLICATE_MESSAGE',lambda:rt.accept_message(message(),T));self.assertEqual(len(rt.audit),n)
    def test_unknown_sender(self):
        rt=runtime();self.reject('INVALID_IDENTITY',lambda:rt.accept_message(message(producer_id='intruder'),T))
