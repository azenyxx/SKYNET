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
        self.assertEqual(identity().worker_id,'worker')
    def test_invalid(self):
        self.reject('INVALID_IDENTITY',lambda:identity(worker_id='../bad'))
    def test_version(self):
        self.reject('UNSUPPORTED_VERSION',lambda:identity(schema_version='v2'))
    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):identity().worker_id='other'
    def test_metadata(self):
        self.reject('INVALID_SCHEMA',lambda:identity(metadata={}))
    def test_capability(self):
        self.reject('CAPABILITY_DENIED',lambda:identity(capability_set=('unknown',)))
