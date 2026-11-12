"""Serial, host-owned copy transaction. Replay starts from a pinned local seed."""
from copy import deepcopy
from dataclasses import asdict
import json
from skynet_sys.canonical import FrozenJSON, digest
from skynet_sys.evidence import EvidenceReference
from skynet_sys.messages import Message
from skynet_sys_memory import Operation
from skynet_sys_workers.integration import Integrated
from skynet_sys_workers.orchestrator import Lease
from skynet_sys_transport.contracts import collection_digest
from .engine import Engine, VerificationRequest, VerificationAssessment, need, VerificationError
from .audit import chunks, snapshot, payload_digest, SubmissionRecord


class IntegratedVerification:
    def __init__(self, engine, workers, actor='admin', namespace='agent'):
        need(type(engine) is Engine and type(workers) is Integrated, 'COMPATIBILITY_LAYOUT')
        self.engine = deepcopy(engine)
        self.workers = deepcopy(workers)
        self.actor = actor
        self.namespace = namespace
        self.sequence = 0
        self.commands = ()
        self._seed = (deepcopy(engine), deepcopy(workers), actor, namespace)
        self.seed_commitment = self.state_digest()
        self.journal_head = digest('integrated-verification-seed-v1', self.seed_commitment)

    def _layout(self):
        """Narrow pinned SYS-005-R2 layout, read-only; no predecessor writes."""
        w = self.workers
        need(type(w) is Integrated and type(w.bindings) is dict and type(w.core.leases) is dict and type(w.core.results) is dict, 'COMPATIBILITY_LAYOUT')
        need(type(w.memory._outbox) is tuple and type(w.memory._journal) is tuple and type(w.bus._journal) is list, 'COMPATIBILITY_LAYOUT')
        need(len(w.bindings) <= 64 and len(w.core.leases) <= 1024, 'COMPATIBILITY_LAYOUT')

    def _binding(self, q, payload, lid):
        self._layout()
        need(type(q) is VerificationRequest, 'REQUEST')
        w = self.workers
        need(lid in w.core.leases and lid in w.bindings, 'LEASE_BINDING')
        lease = w.core.leases[lid]
        need(type(lease) is Lease and type(w.bindings[lid]) is tuple and len(w.bindings[lid]) == 2, 'COMPATIBILITY_LAYOUT')
        need(lease.lease_state == 'COMPLETED' and lease.task_id == q.task_id and lease.worker_id == q.producer_id, 'RESULT_BINDING')
        need(w.core.results.get(lid) == q.result_commitment == digest('worker-result-v1', payload), 'RESULT_COMMITMENT')
        cp = w.scheduler.checkpoint(w.actor)
        cp.verify()
        rows = {}
        for item in cp.tasks:
            row = item.value()
            need(type(row) is list and len(row) == 14 and row[0] not in rows, 'COMPATIBILITY_LAYOUT')
            rows[row[0]] = row
        need(q.task_id in rows, 'TASK_BINDING')
        row = rows[q.task_id]
        need(w.bindings[lid][0] == q.task_id and row[11] == 'SUCCEEDED' and row[8] == q.producer_id and row[9] == w.bindings[lid][1], 'TASK_BINDING')

    def component_digests(self):
        self._layout()
        w = self.workers
        # SYS-005 state_digest() is the actual public contract. Outbox and
        # journal commitments supplement state omitted by predecessor digests.
        return (
            self.engine.state_digest(), w.state_digest(),
            w.scheduler.checkpoint(w.actor).commitment,
            collection_digest('verification-memory-outbox-v1', w.memory._outbox),
            collection_digest('verification-memory-journal-v1', tuple(e.record_hash for e in w.memory._journal)),
            collection_digest('verification-transport-journal-v1', tuple(e.record_hash for e in w.bus._journal)),
            collection_digest('verification-worker-journal-v1', tuple(e.entry_hash for e in w.core.journal)),
        )

    def state_digest(self):
        return digest('integrated-verification-state-v2', (self.component_digests(), self.sequence, self.actor, self.namespace))

    @staticmethod
    def _command_commitment(operation, args, lid, expected):
        if operation == 'open':
            body = (args[0].commitment, digest('worker-result-v1', args[1]))
        elif operation == 'submit':
            body = (payload_digest(snapshot(args[0])), args[1])
        else:
            body = args
        return digest('integrated-verification-command-v1', (operation, body, lid, expected))

    def _operation(self, key, payload, tick, expected=0):
        payload = FrozenJSON.make(payload)
        ref = EvidenceReference(key, self.actor, key, digest('verification-evidence-v1', payload), 'verification-diagnostic', self.workers.bus.config.at(tick), 'UNVERIFIED')
        return Operation(self.namespace, key, 'CREATE', expected, payload, (ref,))

    def run(self, operation, args, lid=None, expected=0):
        need(operation in ('open', 'submit', 'evaluate'), 'OPERATION')
        need(type(args) is tuple and len(args) == 2, 'ARGUMENTS')
        need(type(expected) is int and expected >= 0, 'EXPECTED_VERSION')
        need(self.sequence < 64, 'INTEGRATION_CAPACITY')
        d = deepcopy(self)
        if operation == 'open':
            d._binding(args[0], args[1], lid)
        rid = args[0].request_id if operation in ('open', 'submit') else args[0]
        before_round = d.engine.rounds.get(rid)
        before_submissions = len(before_round['submissions']) if before_round else 0
        before_conflicts = len(before_round['conflict_records']) if before_round else 0
        failure = None
        before = len(d.engine.journal)
        try:
            out = getattr(d.engine, operation)(*args)
        except ValueError as exc:
            if len(d.engine.journal) == before:
                raise
            failure, out = exc, None
        entry = d.engine.journal[-1]
        key = 'verify:' + str(d.sequence)
        new_submissions = d.engine.submission_records(rid)[before_submissions:]
        new_conflicts = d.engine.conflict_records(rid)[before_conflicts:]
        # One summary plus independently addressable full submission, conflict,
        # and decision records; never embed unbounded transcripts in a message.
        recent_audit = tuple(row for row in d.engine.audit_records(rid) if row[1] in {x.submission_id for x in new_submissions} | {x.conflict_id for x in new_conflicts})
        summary = {'operation': operation, 'request_id': rid, 'request_commitment': entry.request_commitment, 'assessment_commitment': entry.assessment_commitment, 'decision_commitment': entry.decision_commitment, 'state_digest': d.engine.state_digest(), 'entry_hash': entry.entry_hash, 'audit_records': recent_audit}
        ops = [d._operation(key, summary, entry.logical_tick, expected)]
        for receipt in new_submissions:
            prefix = key + ':submission'
            ops.append(d._operation(prefix, receipt.metadata(), entry.logical_tick))
            for index, text in enumerate(chunks(receipt.payload_json)):
                ops.append(d._operation(prefix + ':' + str(index), {'index': index, 'data': text, 'payload_commitment': receipt.payload_commitment}, entry.logical_tick))
        for index, conflict in enumerate(new_conflicts):
            ops.append(d._operation(key + ':conflict:' + str(index), conflict.metadata(), entry.logical_tick))
        if operation == 'evaluate':
            ops.append(d._operation(key + ':decision', asdict(out), entry.logical_tick))
        need(len(ops) <= 16, 'INTEGRATION_RECORD_CAPACITY')
        d.workers.memory.transact(d.actor, key, tuple(ops), entry.logical_tick)
        event_payload = {k: v for k, v in summary.items() if k != 'audit_records'}
        event_payload['audit_commitment'] = collection_digest('verification-event-audit-v1', recent_audit)
        message = Message(key, 'verification-trace', None, None, d.actor, d.workers.bus.config.bus_id, 'EVIDENCE_ATTACHED', FrozenJSON.make(event_payload), d.workers.bus.config.at(entry.logical_tick), d.workers.bus.config.at(entry.logical_tick + 1))
        d.workers.bus.publish(d.actor, 'system.audit', message, entry.logical_tick)
        d.sequence += 1
        command = (operation, deepcopy(args), lid, expected, d.state_digest(), entry.entry_hash)
        d.journal_head = digest('integrated-verification-journal-v1', (d.journal_head, d.sequence, d._command_commitment(operation, args, lid, expected), command[4], command[5]))
        d.commands += (command,)
        self.__dict__.update(d.__dict__)
        if failure is not None:
            raise failure
        return out

    def read_submission(self, actor, sequence):
        need(type(sequence) is int and 0 <= sequence < self.sequence, 'SUBMISSION_SEQUENCE')
        prefix = 'verify:' + str(sequence) + ':submission'
        metadata = self.workers.memory.read(actor, self.namespace, prefix).payload.value()
        need(type(metadata.get('chunks')) is int and 1 <= metadata['chunks'] <= 8, 'AUDIT_CHUNKS')
        parts = []
        for index in range(metadata['chunks']):
            part = self.workers.memory.read(actor, self.namespace, prefix + ':' + str(index)).payload.value()
            need(part['index'] == index and part['payload_commitment'] == metadata['payload_commitment'] and type(part['data']) is str and len(part['data']) <= 1024, 'AUDIT_CHUNK_BINDING')
            parts.append(part['data'])
        receipt = SubmissionRecord(metadata['submission_id'], metadata['request_id'], metadata['disposition'], metadata['reason_code'], ''.join(parts), metadata['schema_version'])
        need(receipt.metadata() == metadata, 'AUDIT_RECORD_MISMATCH')
        need(receipt in self.engine.submission_records(receipt.request_id), 'AUDIT_RECORD_BINDING')
        return receipt

    def read_conflict(self, actor, sequence, index=0):
        record = self.workers.memory.read(actor, self.namespace, 'verify:' + str(sequence) + ':conflict:' + str(index)).payload.value()
        matches = [c for rid in self.engine.rounds for c in self.engine.conflict_records(rid) if c.conflict_id == record.get('conflict_id')]
        need(len(matches) == 1 and FrozenJSON.make(matches[0].metadata()).value() == record, 'CONFLICT_RECORD_BINDING')
        return matches[0]

    def replay(self, commands=None):
        entries = self.commands if commands is None else commands
        need(type(entries) is tuple and len(entries) == len(self.commands) <= 64, 'INTEGRATED_REPLAY_MISMATCH')
        out = IntegratedVerification(*deepcopy(self._seed))
        need(out.seed_commitment == self.seed_commitment, 'INTEGRATED_SEED_MISMATCH')
        for index, entry in enumerate(entries):
            need(type(entry) is tuple and len(entry) == 6, 'INTEGRATED_JOURNAL')
            op, args, lid, expected, state, head = entry
            try:
                out.run(op, args, lid, expected)
            except ValueError:
                need(len(out.commands) == index + 1 and out.commands[-1] == entry, 'INTEGRATED_REPLAY_MISMATCH')
            need(len(out.commands) == index + 1 and out.commands[-1] == entry and out.state_digest() == state and out.engine.journal[-1].entry_hash == head, 'INTEGRATED_REPLAY_MISMATCH')
        need(out.journal_head == self.journal_head and out.state_digest() == self.state_digest(), 'INTEGRATED_REPLAY_MISMATCH')
        return out
