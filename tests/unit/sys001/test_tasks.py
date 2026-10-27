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
    def test_chain(self):
        for a,b in [('CREATED','VALIDATED'),('VALIDATED','QUEUED'),('QUEUED','RUNNING'),('RUNNING','SUCCEEDED')]:self.assertTrue(transition(a,b))
    def test_skip(self):
        self.reject('INVALID_TRANSITION',lambda:transition('CREATED','SUCCEEDED'))
    def test_terminal(self):
        self.reject('INVALID_TRANSITION',lambda:transition('SUCCEEDED','RUNNING'))
    def test_duplicate_terminal(self):
        self.assertFalse(transition('FAILED','FAILED'))
    def test_priority_bool(self):
        self.reject('INVALID_SCHEMA',lambda:request(priority=True))
    def test_deadline(self):
        self.reject('INVALID_SCHEMA',lambda:request(deadline=T))
    def test_self_parent(self):
        self.reject('INVALID_SCHEMA',lambda:request(parent_task_id='task'))
    def test_unhashable_result_status(self):
        self.reject('INVALID_SCHEMA',lambda:TaskResult('task','attempt','trace','worker','a'*64,[],P,T))
    def test_result_verified_rejected(self):
        self.reject('EVIDENCE_UNAVAILABLE',lambda:TaskResult('task','attempt','trace','worker','a'*64,'SUCCEEDED',P,T,'VERIFIED'))
