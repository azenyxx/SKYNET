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
    def test_registration(self):
        rt=runtime();self.assertEqual(rt.declaration('worker').capability_set,('system.observe',));self.assertEqual(len(rt.audit),2)
    def test_duplicate_worker(self):
        rt=runtime();self.reject('DUPLICATE_MESSAGE',lambda:rt.register_worker(identity(),T))
    def test_node_required(self):
        rt=Runtime('runtime',HostPolicy('p'));self.reject('INVALID_SCHEMA',lambda:rt.register_worker(identity(),T))
    def test_denied(self):
        rt=runtime(False);self.reject('CAPABILITY_DENIED',lambda:rt.create_task(request(),T));self.assertEqual(rt.audit[-1].action,'CAPABILITY_DENIED');self.reject('INVALID_SCHEMA',lambda:rt.task('task'))
    def test_idempotency(self):
        rt=runtime();rt.create_task(request(),T);self.reject('DUPLICATE_MESSAGE',lambda:rt.create_task(request(task_id='task2'),T))
    def test_complete(self):
        rt=runtime();q=request();rt.create_task(q,T)
        for s in ('VALIDATED','QUEUED','RUNNING'):rt.transition_task('task',s,T)
        x=TaskResult('task','attempt','trace','worker',q.commitment,'SUCCEEDED',P,T);rt.transition_task('task','SUCCEEDED',T,x);n=len(rt.audit);self.assertFalse(rt.transition_task('task','SUCCEEDED',T,x));self.assertEqual(len(rt.audit),n);self.assertEqual(rt.task('task')[2],x)
    def test_result_binding(self):
        rt=runtime();q=request();rt.create_task(q,T)
        for s in ('VALIDATED','QUEUED','RUNNING'):rt.transition_task('task',s,T)
        x=TaskResult('task','attempt','trace','worker','a'*64,'SUCCEEDED',P,T);self.reject('INVALID_TRANSITION',lambda:rt.transition_task('task','SUCCEEDED',T,x));self.assertEqual(rt.task('task')[1],'RUNNING')
    def test_audit_replay(self):
        a=runtime();b=runtime();a.create_task(request(),T);b.create_task(request(),T);self.assertEqual(a.audit,b.audit);self.assertEqual(a.audit[-1].previous_digest,a.audit[-2].commitment)
    def test_expiry(self):
        rt=runtime();rt.create_task(request(),T);self.reject('EXPIRED_MESSAGE',lambda:rt.transition_task('task','VALIDATED',L));rt.transition_task('task','EXPIRED',L);self.assertEqual(rt.task('task')[1],'EXPIRED')
    def test_clock_rollback(self):
        rt=runtime();rt.create_task(request(),T);rt.transition_task('task','EXPIRED',L);self.reject('INVALID_SCHEMA',lambda:rt.checkpoint('cp','task',T))
    def test_terminal_mutation(self):
        rt=runtime();rt.create_task(request(),T);rt.transition_task('task','CANCELLED',T);self.reject('INVALID_TRANSITION',lambda:rt.transition_task('task','FAILED',T));self.assertEqual(rt.task('task')[1],'CANCELLED')
    def test_bounded_registry(self):
        rt=runtime()
        for i in range(255):rt.register_worker(identity(worker_id='w'+str(i)),T)
        n=len(rt.audit);self.reject('INVALID_SCHEMA',lambda:rt.register_worker(identity(worker_id='extra'),T));self.assertEqual(len(rt.audit),n)
    def test_invalid_time_atomic(self):
        rt=Runtime('runtime',HostPolicy('p'))
        self.reject('INVALID_SCHEMA',lambda:rt.register_node(identity('NODE'),None))
        self.assertEqual(rt.audit,())
    def test_message_cannot_dispatch(self):
        rt=runtime();rt.create_task(request(),T)
        rt.accept_message(message(message_type='TASK_COMPLETED'),T)
        self.assertEqual(rt.task('task')[1],'CREATED')
    def test_result_rewrite_rejected(self):
        rt=runtime();q=request();rt.create_task(q,T)
        for s in ('VALIDATED','QUEUED','RUNNING'):rt.transition_task('task',s,T)
        x=TaskResult('task','attempt','trace','worker',q.commitment,'SUCCEEDED',P,T)
        rt.transition_task('task','SUCCEEDED',T,x);n=len(rt.audit)
        self.reject('INVALID_TRANSITION',lambda:rt.transition_task('task','SUCCEEDED',T,replace(x,payload=FrozenJSON.make('changed'))))
        self.assertEqual(rt.task('task')[2],x);self.assertEqual(len(rt.audit),n)
