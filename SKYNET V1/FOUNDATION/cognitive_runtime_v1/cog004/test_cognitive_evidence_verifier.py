import copy
import unittest
from dataclasses import replace,asdict
from unittest.mock import patch
from cognitive_contracts import canonical_bytes
from cognitive_tool_contracts import body_commitment, ToolResultV1
from cognitive_tool_adapter import execute_isolated
from test_cognitive_tool_adapter import fixture as tool_fixture, A, B, R
from cognitive_verification_contracts import *
from cognitive_evidence_verifier import verify_original_evidence

def fixture():
    args=tool_fixture()
    return VerificationRequestV1('cog-verification-request-v1',*args,execute_isolated(*args))
def corrupt(obj,**kw):
    out=copy.copy(obj)
    for name,value in kw.items(): object.__setattr__(out,name,value)
    return out

class VerifierTests(unittest.TestCase):
    def reject(self,v,stage=None):
        d=verify_original_evidence(v)
        self.assertEqual(d.status,'EVIDENCE_REJECTED')
        if stage: self.assertEqual(d.findings[0].stage,stage)
        return d
    def test_positive(self):
        self.assertEqual(verify_original_evidence(fixture()).status,'EVIDENCE_VERIFIED_ISOLATED')
    def test_identity(self):
        v=fixture(); self.assertEqual(verify_original_evidence(v).verification_id,verify_original_evidence(v).verification_id)
    def test_independent_recomputation(self):
        v=fixture()
        with patch('cognitive_tool_adapter.execute_isolated',side_effect=AssertionError),patch('cognitive_tool_adapter.verify_evidence',side_effect=AssertionError):
            self.assertEqual(verify_original_evidence(v).status,'EVIDENCE_VERIFIED_ISOLATED')
    def test_input(self):
        v=fixture(); self.reject(replace(v,request=corrupt(v.request,text='changed')),'REQUEST')
    def test_digest(self):
        v=fixture(); self.reject(replace(v,evidence=corrupt(v.evidence,result=corrupt(v.evidence.result,sha256_hex='0'*64))),'EVIDENCE')
    def test_rehashed_false_output(self):
        v=fixture()
        result=corrupt(v.evidence.result,sha256_hex='0'*64)
        result=replace(result,commitment=body_commitment(b'SKYNET:COGToolResultV1:v1\0',result))
        e=corrupt(v.evidence,result=result)
        e=replace(e,commitment=body_commitment(b'SKYNET:COGToolEvidenceV1:v1\0',e))
        self.reject(replace(v,evidence=e),'RECOMPUTE')
    def test_evidence_commitment(self):
        v=fixture(); self.reject(replace(v,evidence=corrupt(v.evidence,commitment='0'*64)),'EVIDENCE')
    def test_result_commitment(self):
        v=fixture(); self.reject(replace(v,evidence=corrupt(v.evidence,result=corrupt(v.evidence.result,commitment='0'*64))),'EVIDENCE')
    def test_task(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,task_id=B)),'REQUEST')
    def test_plan(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,plan_id='0'*64)),'REQUEST')
    def test_step(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,step_id=R)),'REQUEST')
    def test_stale(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,progress_revision=1)),'REQUEST')
    def test_definition(self):
        v=fixture(); p=replace(v.plan,steps=(replace(v.plan.steps[0],operation='SYNTHESIZE'),v.plan.steps[1]))
        self.reject(replace(v,plan=p),'PLAN')
    def test_fabricated_decision(self):
        self.reject(verify_original_evidence(fixture()),'INPUT')
        v=fixture(); self.reject(corrupt(v,evidence=verify_original_evidence(v)),'INPUT')
    def test_operation(self):
        v=fixture(); self.reject(replace(v,request=corrupt(v.request,operation='EXEC')),'REQUEST')
    def test_version(self):
        v=fixture(); self.reject(replace(v,evidence=corrupt(v.evidence,schema_version='v2')),'EVIDENCE')
    def test_malformed(self): self.reject({'success':True},'INPUT')
    def test_oversized(self):
        v=fixture(); self.reject(replace(v,request=corrupt(v.request,text='é'*2049)),'REQUEST')
    def test_no_mutation(self):
        v=fixture(); before=asdict(v); verify_original_evidence(v); self.assertEqual(asdict(v),before)
    def test_no_authority(self): self.assertFalse(verify_original_evidence(fixture()).production_authorized)
    def test_no_trusted(self): self.assertFalse(verify_original_evidence(fixture()).trusted_verification)
    def test_no_completion(self):
        v=fixture(); d=verify_original_evidence(v)
        self.assertFalse(d.task_completion_authorized); self.assertEqual(v.state.task.status,'VALIDATED')
        self.assertEqual(v.progress.revision,0)
    def test_taxonomy(self):
        v=fixture(); v=replace(v,request=corrupt(v.request,text='secret'))
        a=self.reject(v); b=self.reject(v); self.assertEqual(a,b); self.assertEqual(a.findings[0].code,'INVALID_REQUEST')
    def test_no_sensitive_findings(self):
        v=fixture(); secret='sensitive-private-input'
        d=self.reject(replace(v,request=corrupt(v.request,text=secret)))
        self.assertNotIn(secret,canonical_bytes(d).decode())
    def test_missing(self):
        d=verify_original_evidence(replace(fixture(),binding=None))
        self.assertEqual(d.status,'VERIFICATION_DEPENDENCY_UNAVAILABLE')
    def test_invalid_utf8(self):
        v=fixture(); self.reject(replace(v,request=corrupt(v.request,text='\ud800')),'REQUEST')
    def test_nonready(self):
        v=fixture(); self.reject(replace(v,request=replace(v.request,step_id=B)),'REQUEST')
    def test_binding(self):
        v=fixture(); self.reject(replace(v,binding=replace(v.binding,progress_digest='0'*64)),'BINDING')
    def test_task_snapshot(self):
        v=fixture(); self.reject(replace(v,state=corrupt(v.state,events=())),'TASK')
    def test_no_io(self):
        v=fixture()
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError),patch('subprocess.Popen',side_effect=AssertionError):
            self.assertEqual(verify_original_evidence(v).status,'EVIDENCE_VERIFIED_ISOLATED')
    def test_unknown_fields(self):
        with self.assertRaises(TypeError): VerificationRequestV1(**(asdict(fixture())|{'success':True}))
