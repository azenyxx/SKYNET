"""Completion regressions use real predecessor fixtures, not mocked success."""
import unittest
from copy import deepcopy
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch
import json
from test_verification import engine, req, payload, assessment
import test_verification as predecessor_fixture
from skynet_sys_verification import Engine, VerificationError, Policy, HostPolicy, VerificationAssessment, digest, FrozenJSON
from skynet_sys_verification.audit import snapshot, MAX_SUBMISSION_BYTES
from skynet_sys_verification.integration import IntegratedVerification
from skynet_sys_memory import Operation, MemoryError
from skynet_sys.errors import ContractError
from skynet_sys_transport.contracts import BusError

class AuditTests(unittest.TestCase):
    def fixture(self, limit=32):
        original=engine();e=Engine(original.authority, original.policies, audit_limit=limit);q=req();e.open(q,payload());return e,q
    def reject(self,e,a,code):
        with self.assertRaisesRegex(ValueError, '^'+code+'$'):e.submit(a,0)
    def test_full_rejected_fields(self):
        e,q=self.fixture();a=assessment(q,'v9');self.reject(e,a,'VERIFIER');r=e.submission_records('r')[0];self.assertEqual(r.payload_json,snapshot(a));v=json.loads(r.payload_json)['fields'];self.assertEqual(v['verifier_id'],'v9');self.assertEqual(v['evidence_refs']['items'][0]['fields']['verification_status'],'UNVERIFIED');self.assertEqual(r.disposition,'REJECTED')
    def test_multiple_rejections_referenced(self):
        e,q=self.fixture()
        for i in range(3):self.reject(e,assessment(q,'v9',aid='bad'+str(i)),'VERIFIER')
        decision=e.evaluate('r',0);self.assertEqual(decision.rejected_assessments,tuple(r.submission_id for r in e.submission_records('r')));self.assertEqual(decision.accepted_assessments,());self.assertEqual(decision.final_verdict,'INCONCLUSIVE')
    def test_audit_saturation_blocks_valid_vote(self):
        e,q=self.fixture(1);self.reject(e,assessment(q,'v9'),'VERIFIER');before=e.state_digest();journal=e.journal
        self.reject(e,assessment(q),'AUDIT_CAPACITY');self.assertEqual(before,e.state_digest());self.assertEqual(journal,e.journal);self.assertEqual(len(e.rounds['r']['assessments']),0)
    def test_saturation_overrides_semantic_error(self):
        e,q=self.fixture(1);self.reject(e,assessment(q,'v9'),'VERIFIER');self.reject(e,assessment(q,'v9'),'AUDIT_CAPACITY');self.assertEqual(len(e.submission_records('r')),1)
    def test_rejected_reference_limit(self):
        e,q=self.fixture()
        for i in range(16):self.reject(e,assessment(q,'v9',aid='bad'+str(i)),'VERIFIER')
        self.reject(e,assessment(q),'AUDIT_CAPACITY');self.assertEqual(len(e.evaluate('r',0).rejected_assessments),16)
    def test_capacity_does_not_prevent_terminal_decision(self):
        e,q=self.fixture(1);e.submit(assessment(q),0);self.assertEqual(e.evaluate('r',0).final_verdict,'PASS')
    def test_malformed_known_envelope_audited(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'schema_version','unsupported');self.reject(e,a,'SCHEMA');self.assertEqual(json.loads(e.submission_records('r')[0].payload_json)['fields']['schema_version'],'unsupported')
    def test_malformed_evidence_member_audited(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'evidence_refs',(12,));self.reject(e,a,'INVALID_SCHEMA');self.assertEqual(e.submission_records('r')[0].payload_json,snapshot(a))
    def test_invalid_reason_type_audited(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'reason_codes',(['bad'],));self.reject(e,a,'IDENTIFIERS');self.assertEqual(len(e.submission_records('r')),1)
    def test_oversize_not_admitted(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'reason_codes',tuple('x'*4096 for _ in range(4)));before=e.state_digest();self.reject(e,a,'AUDIT_PAYLOAD_SIZE');self.assertEqual(before,e.state_digest());self.assertEqual(e.submission_records('r'),())
    def test_unsupported_object_not_admitted(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'reason_codes',(object(),));before=e.state_digest();self.reject(e,a,'AUDIT_ENCODING');self.assertEqual(before,e.state_digest())
    def test_journal_saturation_fail_closed(self):
        e,q=self.fixture();e.journal=e.journal*1024;before=e.state_digest();self.reject(e,assessment(q),'JOURNAL_CAPACITY');self.assertEqual(before,e.state_digest())
    def test_rejection_receipt_immutable(self):
        e,q=self.fixture();self.reject(e,assessment(q,'v9'),'VERIFIER')
        with self.assertRaises(FrozenInstanceError):e.submission_records('r')[0].disposition='ACCEPTED'
    def test_conflict_contains_all_bindings(self):
        e,q=self.fixture();a=assessment(q);b=replace(a,verdict='FAIL');e.submit(a,0);e.submit(b,0);c=e.conflict_records('r')[0];self.assertEqual(c.references,(a.assessment_commitment,b.assessment_commitment));self.assertEqual(c.reason_code,'ASSESSMENT_REVISION_CONFLICT');self.assertEqual(e.submission_records('r')[1].payload_json,snapshot(b))
    def test_conflict_cannot_count_reused_identity(self):
        e,q=self.fixture();e.submit(assessment(q),0);e.submit(replace(assessment(q),assessment_id='reuse'),0);d=e.evaluate('r',0);self.assertEqual(len(d.accepted_assessments),1);self.assertEqual(len(d.rejected_assessments),1);self.assertEqual(d.final_verdict,'INCONCLUSIVE')
    def test_malformed_submission_replay(self):
        e,q=self.fixture();a=assessment(q);object.__setattr__(a,'schema_version','bad');self.reject(e,a,'SCHEMA');self.assertEqual(e.state_digest(),e.replay(e.journal).state_digest())
    def test_rejection_payload_tamper_rejected(self):
        e,q=self.fixture();a=assessment(q,'v9');self.reject(e,a,'VERIFIER');entry=e.journal[-1];altered=replace(a,reason_codes=('CHANGED',));entries=e.journal[:-1]+(replace(entry,command=(altered,0)),)
        with self.assertRaisesRegex(VerificationError,'^REPLAY_MISMATCH$'):e.replay(entries)
    def test_audit_limit_bound_to_replay(self):
        e,q=self.fixture(1);self.reject(e,assessment(q,'v9'),'VERIFIER');self.assertEqual(e.replay(e.journal).audit_limit,1);self.assertEqual(e.replay(e.journal).state_digest(),e.state_digest())

class CompositeTests(unittest.TestCase):
    def fixture(self):return predecessor_fixture.IntegrationTests().fixture()
    def open(self):
        i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);return i,q,l
    def test_original_api_digest(self):
        i,q,l=self.open();self.assertEqual(i.component_digests()[1],i.workers.state_digest())
    def test_full_rejected_memory_roundtrip(self):
        i,q,l=self.open();a=assessment(q,'v9')
        with self.assertRaisesRegex(VerificationError,'^VERIFIER$'):i.run('submit',(a,0))
        r=i.read_submission('admin',1);self.assertEqual(r.payload_json,snapshot(a));self.assertEqual(r.disposition,'REJECTED');self.assertEqual(i.state_digest(),i.replay().state_digest())
    def test_large_rejected_memory_roundtrip(self):
        i,q,l=self.open();a=assessment(q,'v9');object.__setattr__(a,'reason_codes',('a'*4096,))
        with self.assertRaisesRegex(ContractError,'^INVALID_IDENTITY$'):i.run('submit',(a,0))
        self.assertEqual(i.read_submission('admin',1).payload_json,snapshot(a))
    def test_accepted_memory_roundtrip(self):
        i,q,l=self.open();a=assessment(q);i.run('submit',(a,0));self.assertEqual(i.read_submission('admin',1).payload_json,snapshot(a));self.assertEqual(i.read_submission('admin',1).disposition,'ACCEPTED')
    def test_conflict_memory_query(self):
        i,q,l=self.open();a=assessment(q);i.run('submit',(a,0));i.run('submit',(replace(a,verdict='FAIL'),0));c=i.read_conflict('admin',2);self.assertEqual(c.reason_code,'ASSESSMENT_REVISION_CONFLICT');self.assertEqual(c.references,(a.assessment_commitment,replace(a,verdict='FAIL').assessment_commitment));self.assertEqual(i.read_submission('admin',2).disposition,'REJECTED')
    def test_decision_memory_query(self):
        i,q,l=self.open();i.run('submit',(assessment(q),0));d=i.run('evaluate',('r',0));stored=i.workers.memory.read('admin','agent','verify:2:decision').payload.value();self.assertEqual(stored['final_verdict'],d.final_verdict);self.assertEqual(stored['accepted_assessments'],list(d.accepted_assessments))
    def test_acl_protects_full_rejection(self):
        i,q,l=self.open();i.run('submit',(assessment(q),0))
        with self.assertRaisesRegex(MemoryError,'^DENIED$'):i.read_submission('w',1)
    def test_cas_failure_rolls_back_complete_state(self):
        i,q,l=self.open();i.workers.memory.transact('admin','external',(Operation('agent','verify:1','CREATE',0,FrozenJSON.make({})),),0);before=i.state_digest();head=i.journal_head
        with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):i.run('submit',(assessment(q,'v9'),0))
        self.assertEqual(i.state_digest(),before);self.assertEqual(i.journal_head,head);self.assertEqual(i.engine.submission_records('r'),())
    def test_backpressure_rolls_back_rejection(self):
        i,q,l=self.open();i.workers.bus.config=replace(i.workers.bus.config,queue_limit=1);before=i.state_digest();commands=i.commands
        with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):i.run('submit',(assessment(q,'v9'),0))
        self.assertEqual(before,i.state_digest());self.assertEqual(commands,i.commands);self.assertEqual(i.engine.submission_records('r'),())
    def test_saturation_atomic_all_components(self):
        i,q,l=self.fixture();e=i.engine;i=IntegratedVerification(Engine(e.authority,e.policies,audit_limit=1),i.workers);i.run('open',(q,payload()),l.lease_id)
        with self.assertRaisesRegex(VerificationError,'^VERIFIER$'):i.run('submit',(assessment(q,'v9'),0))
        before=i.state_digest()
        with self.assertRaisesRegex(VerificationError,'^AUDIT_CAPACITY$'):i.run('submit',(assessment(q),0))
        self.assertEqual(before,i.state_digest());self.assertEqual(i.state_digest(),i.replay().state_digest())
    def test_conflict_replay_every_component(self):
        i,q,l=self.open();a=assessment(q);i.run('submit',(a,0));i.run('submit',(replace(a,verdict='FAIL'),0));i.run('evaluate',('r',0));out=i.replay();self.assertEqual(i.component_digests(),out.component_digests());self.assertEqual(i.journal_head,out.journal_head);self.assertEqual(i.engine.decision('r').final_verdict,'INCONCLUSIVE')
    def test_replay_cannot_truncate(self):
        i,q,l=self.open()
        with self.assertRaisesRegex(VerificationError,'^INTEGRATED_REPLAY_MISMATCH$'):i.replay(())
    def test_replay_cannot_duplicate(self):
        i,q,l=self.open()
        with self.assertRaisesRegex(VerificationError,'^INTEGRATED_REPLAY_MISMATCH$'):i.replay(i.commands+i.commands)
    def test_replay_cannot_change_seed(self):
        i,q,l=self.open();i._seed[0].tick=1
        with self.assertRaisesRegex(VerificationError,'^INTEGRATED_SEED_MISMATCH$'):i.replay()
    def test_replay_cannot_change_command_reason(self):
        i,q,l=self.open();a=assessment(q);i.run('submit',(a,0));c=i.commands[-1];changed=(c[0],(replace(a,reason_codes=('OTHER',)),0))+c[2:]
        with self.assertRaisesRegex(VerificationError,'^INTEGRATED_REPLAY_MISMATCH$'):i.replay(i.commands[:-1]+(changed,))
    def test_no_worker_execution_on_replay(self):
        i,q,l=self.open();i.run('submit',(assessment(q),0));i.run('evaluate',('r',0));before=i.state_digest()
        with patch.object(type(i.workers),'complete',side_effect=AssertionError('WORKER_EXECUTION')),patch.object(type(i.workers),'dispatch',side_effect=AssertionError('WORKER_EXECUTION')):
            out=i.replay()
        self.assertEqual(before,i.state_digest());self.assertEqual(out.state_digest(),before)
    def test_layout_mismatch_fail_closed(self):
        i,q,l=self.fixture();i.workers.bindings=[]
        with self.assertRaisesRegex(VerificationError,'^COMPATIBILITY_LAYOUT$'):i.run('open',(q,payload()),l.lease_id)
    def test_chunk_corruption_query_rejected(self):
        i,q,l=self.open();i.run('submit',(assessment(q),0));rec=i.workers.memory.read('admin','agent','verify:1:submission:0');value=rec.payload.value();value['payload_commitment']='f'*64;i.workers.memory.transact('admin','tamper',(Operation('agent','verify:1:submission:0','UPDATE',rec.version,FrozenJSON.make(value)),),0)
        with self.assertRaisesRegex(VerificationError,'^AUDIT_CHUNK_BINDING$'):i.read_submission('admin',1)

class PolicyIntegrationTests(unittest.TestCase):
    def fixture(self,kind,threshold=1):
        base,q,lease=predecessor_fixture.IntegrationTests().fixture()
        voters=tuple('v'+str(i) for i in range(10))
        if kind=='SINGLE_AUTHORIZED':voters=('v9',)
        authority=HostPolicy('ten-integration',(('w','cognitive.reason'),)+tuple((v,'cognitive.verify') for v in voters))
        e=Engine(authority,(Policy('policy',kind,voters,threshold),))
        i=IntegratedVerification(e,base.workers);q=replace(q,policy_id='policy');i.run('open',(q,payload()),lease.lease_id);return i,q
    def test_real_ten_verifier_unanimous(self):
        i,q=self.fixture('UNANIMOUS')
        for n in range(10):i.run('submit',(assessment(q,'v'+str(n)),0))
        self.assertEqual(i.run('evaluate',('r',0)).final_verdict,'PASS');self.assertEqual(len({a.verifier_id for a in i.engine.rounds['r']['assessments']}),10);self.assertEqual(i.component_digests(),i.replay().component_digests())
        print('INTEGRATED_TEN '+json.dumps({'participants':10,'policy':'UNANIMOUS','verdict':'PASS','digest':i.state_digest(),'replay_digest':i.replay().state_digest()}))
    def test_real_ten_quorum(self):
        i,q=self.fixture('QUORUM',10)
        for n in range(10):i.run('submit',(assessment(q,'v'+str(n),'FAIL'),0))
        self.assertEqual(i.run('evaluate',('r',0)).final_verdict,'FAIL');self.assertEqual(i.state_digest(),i.replay().state_digest())
    def test_real_single_authorized_ninth_identity(self):
        i,q=self.fixture('SINGLE_AUTHORIZED');i.run('submit',(assessment(q,'v9'),0));self.assertEqual(i.run('evaluate',('r',0)).final_verdict,'PASS')
    def test_real_insufficient_quorum(self):
        i,q=self.fixture('QUORUM',10)
        for n in range(9):i.run('submit',(assessment(q,'v'+str(n)),0))
        self.assertEqual(i.run('evaluate',('r',0)).final_verdict,'INCONCLUSIVE')
    def test_real_duplicate_identity_not_counted(self):
        i,q=self.fixture('QUORUM',2);a=assessment(q,'v0');i.run('submit',(a,0));i.run('submit',(replace(a,assessment_id='other'),0));d=i.run('evaluate',('r',0));self.assertEqual(d.final_verdict,'INCONCLUSIVE');self.assertEqual(len(d.accepted_assessments),1);self.assertEqual(len(d.rejected_assessments),1)
    def test_real_opposite_votes_conflict(self):
        i,q=self.fixture('QUORUM',2);i.run('submit',(assessment(q,'v0'),0));i.run('submit',(assessment(q,'v1','FAIL'),0));d=i.run('evaluate',('r',0));self.assertEqual(d.final_verdict,'INCONCLUSIVE');self.assertTrue(d.conflict_refs);self.assertEqual(i.read_conflict('admin',2).reason_code,'OPPOSITE_VERDICTS');self.assertEqual(i.state_digest(),i.replay().state_digest())
    def test_terminal_decision_immutable_across_components(self):
        i,q=self.fixture('SINGLE_AUTHORIZED');i.run('submit',(assessment(q,'v9'),0));d=i.run('evaluate',('r',0));before=i.state_digest()
        with self.assertRaisesRegex(VerificationError,'^TERMINAL$'):i.run('submit',(assessment(q,'v9','FAIL'),0))
        self.assertEqual(i.engine.decision('r'),d);self.assertEqual(i.state_digest(),before)
