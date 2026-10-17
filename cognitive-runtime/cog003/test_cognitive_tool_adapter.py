import unittest
import json
import hashlib
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch
from cognitive_contracts import ContractError, canonical_bytes
from cognitive_planner import construct_plan,initial_progress
from test_cognitive_planner import fixture as plan_fixture, A, B
from cognitive_tool_contracts import *
from cognitive_tool_adapter import execute_isolated,verify_evidence

R='00000000-0000-0000-0000-000000000003'
def fixture(text='abc'):
    state,steps=plan_fixture()
    plan=construct_plan(state,steps); progress=initial_progress(plan)
    request=ToolRequestV1('cog-tool-request-v1',A,plan.plan_id,A,0,'SHA256_TEXT_V1',input_digest(text),R,text)
    binding=IsolatedToolBindingV1('cog-isolated-tool-binding-v1','ISOLATED_LOCAL_ONLY',plan.plan_id,A,'ANALYZE','SHA256_TEXT_V1',request_commitment(request),progress_commitment(progress))
    return state,plan,progress,request,binding

class AdapterTests(unittest.TestCase):
    def test_positive(self):
        args=fixture(); e=execute_isolated(*args)
        self.assertEqual(e.result.sha256_hex,'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(e.result.input_byte_length,3); self.assertTrue(verify_evidence(*args,e))
    def test_deterministic(self):
        args=fixture(); self.assertEqual(execute_isolated(*args),execute_isolated(*args))
    def test_binding(self):
        args=fixture(); self.assertEqual(execute_isolated(*args).decision.request_digest,request_commitment(args[3]))
    def changed_request(self,**kw):
        s,p,g,r,b=fixture()
        with self.assertRaises(ContractError): execute_isolated(s,p,g,replace(r,**kw),b)
    def test_wrong_plan(self): self.changed_request(plan_id='0'*64)
    def test_wrong_task(self): self.changed_request(task_id=B)
    def test_wrong_step(self): self.changed_request(step_id=R)
    def test_stale(self): self.changed_request(progress_revision=1)
    def test_nonready(self): self.changed_request(step_id=B)
    def test_unknown(self): self.changed_request(operation='SHELL')
    def test_oversize(self):
        with self.assertRaises(ContractError): fixture('é'*2049)
    def test_invalid_utf8(self):
        with self.assertRaisesRegex(ContractError,'INVALID_UTF8'): fixture('\ud800')
        with self.assertRaises(ContractError): parse_request(b'\xff')
    def test_malformed(self):
        with self.assertRaises(ContractError): parse_request(b'[]')
        with self.assertRaises(ContractError): fixture(b'abc')
    def test_fabricated_decision(self):
        s,p,g,r,b=fixture(); d=execute_isolated(s,p,g,r,b).decision
        with self.assertRaises(ContractError): execute_isolated(s,p,g,d,b)
        with self.assertRaises(ContractError): execute_isolated(s,p,g,r,d)
    def test_no_task_mutation(self):
        args=fixture(); old=canonical_bytes(args[0]); execute_isolated(*args); self.assertEqual(old,canonical_bytes(args[0]))
    def test_no_plan_mutation(self):
        args=fixture(); old=(canonical_bytes(args[1]),canonical_bytes(args[2])); execute_isolated(*args)
        self.assertEqual(old,(canonical_bytes(args[1]),canonical_bytes(args[2])))
    def test_no_completion(self):
        args=fixture(); execute_isolated(*args)
        self.assertEqual(args[2].revision,0); self.assertEqual(args[2].steps[0].status,'PENDING')
    def test_no_production(self):
        e=execute_isolated(*fixture())
        self.assertFalse(e.production_authorized); self.assertFalse(e.result.production_authorized); self.assertFalse(e.decision.production_authorized)
    def test_no_implicit_binding(self):
        s,p,g,r,b=fixture()
        with self.assertRaises(ContractError): execute_isolated(s,p,g,r,None)
        with self.assertRaises(ContractError): execute_isolated(s,p,g,r,replace(b,symbolic_operation='SYNTHESIZE'))
    def test_changed_definition(self):
        s,p,g,r,b=fixture()
        p=replace(p,steps=(replace(p.steps[0],operation='SYNTHESIZE'),p.steps[1]))
        with self.assertRaises(ContractError): execute_isolated(s,p,g,r,b)
    def test_input_digest(self): self.changed_request(canonical_input_digest='0'*64)
    def test_unknown_fields(self):
        body=json.loads(canonical_bytes(fixture()[3])); body['allow']=True
        with self.assertRaises(ContractError): parse_request(json.dumps(body).encode())
    def test_duplicate_fields(self):
        with self.assertRaises(ContractError): parse_request(b'{"a":1,"a":2}')
    def test_roundtrip(self):
        r=fixture()[3]; self.assertEqual(parse_request(canonical_bytes(r)),r)
    def test_byte_boundary(self):
        e=execute_isolated(*fixture('é'*2048)); self.assertEqual(e.result.input_byte_length,4096)
    def test_empty_and_control(self):
        for text in ('','\n\x00'):
            e=execute_isolated(*fixture(text)); self.assertEqual(e.result.sha256_hex,hashlib.sha256(text.encode()).hexdigest())
    def test_bool_revision(self): self.changed_request(progress_revision=True)
    def test_identifier(self): self.changed_request(request_id='bad')
    def test_commitment_tamper(self):
        e=execute_isolated(*fixture())
        with self.assertRaises(ContractError): replace(e,commitment='0'*64)
    def test_no_io(self):
        args=fixture()
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError),patch('subprocess.Popen',side_effect=AssertionError):
            execute_isolated(*args)
    def test_frozen(self):
        e=execute_isolated(*fixture())
        with self.assertRaises(FrozenInstanceError): e.production_authorized=True
