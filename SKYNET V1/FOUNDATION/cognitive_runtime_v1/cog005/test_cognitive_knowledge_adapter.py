import ast
import json
import unittest
from pathlib import Path
from dataclasses import replace, asdict, FrozenInstanceError
from unittest.mock import patch
from cognitive_contracts import ContractError,canonical_bytes
from cognitive_knowledge_contracts import *
from cognitive_knowledge_adapter import propose_knowledge
from cognitive_evidence_verifier import verify_original_evidence
from cognitive_verification_contracts import VerificationRequestV1
from cognitive_tool_adapter import execute_isolated
from test_cognitive_evidence_verifier import fixture,corrupt
from test_cognitive_tool_adapter import fixture as tool_fixture,A,B,R

class KnowledgeTests(unittest.TestCase):
    def reject(self,v,**kw):
        d=propose_knowledge(v,**kw); self.assertEqual(d.status,'KNOWLEDGE_REJECTED'); self.assertIsNone(d.proposal)
    def test_positive(self):
        d=propose_knowledge(fixture()); self.assertEqual(d.status,'KNOWLEDGE_PROPOSED_ISOLATED'); self.assertEqual(d.proposal.knowledge_category,'COMPUTED_FACT_ISOLATED')
    def test_identity(self):
        v=fixture(); self.assertEqual(propose_knowledge(v).proposal.proposal_id,propose_knowledge(v).proposal.proposal_id)
    def test_relation(self):
        p=propose_knowledge(fixture()).proposal
        self.assertEqual(p.proposed_content.relation,'SHA256_OF_UTF8_INPUT')
        self.assertEqual(p.proposed_content.sha256_hex,'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(p.proposed_content.input_byte_length,3)
    def test_exact_evidence(self):
        v=fixture(); p=propose_knowledge(v).proposal; d=verify_original_evidence(v)
        self.assertEqual(p.evidence.input_commitment,v.request.canonical_input_digest)
        self.assertEqual(p.evidence.result_commitment,v.evidence.result.commitment)
        self.assertEqual(p.evidence.evidence_commitment,v.evidence.commitment)
        self.assertEqual(p.evidence.verification_decision_commitment,d.verification_id)
        self.assertEqual((p.task_id,p.plan_id,p.step_id,p.tool_request_id),(v.request.task_id,v.request.plan_id,v.request.step_id,v.request.request_id))
    def test_input(self):
        v=fixture(); self.reject(replace(v,request=corrupt(v.request,text='changed')))
    def test_result(self):
        v=fixture(); self.reject(replace(v,evidence=corrupt(v.evidence,result=corrupt(v.evidence.result,sha256_hex='0'*64))))
    def test_task(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,task_id=B)))
    def test_plan(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,plan_id='0'*64)))
    def test_step(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,step_id=R)))
    def test_stale(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,progress_revision=1)))
    def test_fabricated_positive(self): self.reject(verify_original_evidence(fixture()))
    def test_trusted(self):
        self.reject(fixture(),category='VERIFIED_TRUSTED')
        with self.assertRaises(ContractError): replace(propose_knowledge(fixture()).proposal,knowledge_category='VERIFIED_TRUSTED')
    def test_unknown(self): self.reject(fixture(),category='UNIVERSAL_TRUTH')
    def test_observation(self): self.reject(fixture(),category='OBSERVATION_UNTRUSTED')
    def test_provenance(self):
        self.reject(fixture(),provenance='TRUSTED')
        with self.assertRaises(ContractError): replace(propose_knowledge(fixture()).proposal,provenance_classification='TRUSTED')
    def test_content_bound(self):
        p=propose_knowledge(fixture()).proposal
        with self.assertRaises(ContractError): replace(p.proposed_content,input_byte_length=4097)
        with self.assertRaises(ContractError): replace(p,proposed_content='x'*10000)
    def test_no_memory_writes(self):
        v=fixture()
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError):
            self.assertFalse(propose_knowledge(v).persisted)
    def test_no_world_import(self):
        tree=ast.parse(Path(__file__).with_name('cognitive_knowledge_adapter.py').read_text())
        mods=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('world' in (m or '') or 'services' in (m or '') for m in mods))
    def test_no_mutation(self):
        v=fixture(); before=asdict(v); propose_knowledge(v); self.assertEqual(before,asdict(v))
    def test_no_authority(self):
        d=propose_knowledge(fixture()); self.assertFalse(d.production_authorized); self.assertFalse(d.trusted_knowledge); self.assertFalse(d.proposal.trusted_knowledge)
    def test_no_semantics(self):
        text='The moon is made of cheese'
        args=tool_fixture(text)
        v=VerificationRequestV1('cog-verification-request-v1',*args,execute_isolated(*args))
        p=propose_knowledge(v).proposal
        self.assertNotIn(text,canonical_bytes(p).decode())
        self.assertEqual(p.proposed_content.relation,'SHA256_OF_UTF8_INPUT')
    def test_missing(self):
        self.assertEqual(propose_knowledge(replace(fixture(),binding=None)).status,'KNOWLEDGE_DEPENDENCY_UNAVAILABLE')
    def test_roundtrip(self):
        p=propose_knowledge(fixture()).proposal; self.assertEqual(parse_proposal(canonical_bytes(p)),p)
    def test_unknown_fields(self):
        body=json.loads(canonical_bytes(propose_knowledge(fixture()).proposal)); body['approved']=True
        with self.assertRaises(ContractError): parse_proposal(json.dumps(body).encode())
    def test_duplicate_fields(self):
        with self.assertRaises(ContractError): parse_proposal(b'{"x":1,"x":2}')
    def test_immutable(self):
        p=propose_knowledge(fixture()).proposal
        with self.assertRaises(FrozenInstanceError): p.proposal_revision=2
    def test_distinct_request_identity(self):
        from cognitive_tool_contracts import request_commitment
        v=fixture(); p=propose_knowledge(v).proposal
        req=replace(v.request,request_id=B); binding=replace(v.binding,request_digest=request_commitment(req))
        args=(v.state,v.plan,v.progress,req,binding)
        other=VerificationRequestV1('cog-verification-request-v1',*args,execute_isolated(*args))
        self.assertNotEqual(p.proposal_id,propose_knowledge(other).proposal.proposal_id)
    def test_rechecks_without_execution(self):
        v=fixture()
        with patch('cognitive_tool_adapter.execute_isolated',side_effect=AssertionError):
            self.assertEqual(propose_knowledge(v).status,'KNOWLEDGE_PROPOSED_ISOLATED')
