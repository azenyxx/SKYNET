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
    def test_ordering(self):
        self.assertEqual(canonical({'b':2,'a':1}),canonical({'a':1,'b':2}))
    def test_nan(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(float('nan')))
    def test_infinity(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(float('inf')))
    def test_float(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(0.5))
    def test_object(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(object()))
    def test_key_type(self):
        self.reject('INVALID_SCHEMA',lambda:canonical({1:'x'}))
    def test_depth(self):
        v=0
        for _ in range(10):v=[v]
        self.reject('INVALID_SCHEMA',lambda:canonical(v))
    def test_payload_snapshot(self):
        d={'a':[1]};p=FrozenJSON.make(d);d['a'].append(2);self.assertEqual(p.value(),{'a':[1]})
    def test_domain(self):
        self.assertNotEqual(digest('A',P),digest('B',P))
    def test_oversize(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(['x'*4096]*5))
    def test_noncanonical(self):
        self.reject('INVALID_SCHEMA',lambda:FrozenJSON(b'{"a": 1}'))
    def test_timestamp_zone(self):
        self.reject('INVALID_SCHEMA',lambda:timestamp('2026-10-25T00:00:00+06:00'))
    def test_unicode(self):
        self.assertIn('Б'.encode(),canonical({'name':'Б'}))
    def test_overflow(self):
        self.reject('INVALID_SCHEMA',lambda:canonical(2**63))
    def test_surrogate_key(self):
        self.reject('INVALID_SCHEMA',lambda:canonical({'\ud800':1}))
    def test_duplicate_json_keys(self):
        self.reject('INVALID_SCHEMA',lambda:FrozenJSON(b'{"a":1,"a":1}'))
    def test_invalid_calendar(self):
        self.reject('INVALID_SCHEMA',lambda:timestamp('2026-02-30T00:00:00.000000Z'))
