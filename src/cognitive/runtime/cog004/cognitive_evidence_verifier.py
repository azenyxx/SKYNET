"""Independent recomputation: deliberately no import of the execution adapter."""
from hashlib import sha256
import json
from cognitive_contracts import ContractError, require
from cognitive_planner import construct_plan, ready_steps
from cognitive_tool_contracts import (
    encoded_text, input_digest, request_commitment, progress_commitment, commitment,
)
from cognitive_verification_contracts import (
    VerificationRequestV1, VerificationFindingV1, VerificationDecisionV1,
)

# Fixed taxonomy. No caller text or exception message enters a finding.
TAXONOMY = (
    ('INPUT','INVALID_INPUT','Invalid verification request.'),
    ('TASK','INVALID_TASK','Task snapshot validation failed.'),
    ('PLAN','INVALID_PLAN','Plan or progress validation failed.'),
    ('REQUEST','INVALID_REQUEST','Tool request or revision binding failed.'),
    ('BINDING','INVALID_BINDING','Explicit isolated binding failed.'),
    ('EVIDENCE','INVALID_EVIDENCE','Evidence structure or commitment failed.'),
    ('RECOMPUTE','OUTPUT_MISMATCH','Recomputed output or evidence differs.'),
)

def _decision(status,code,stage,description,evidence=None,request=None):
    finding=VerificationFindingV1('cog-verification-finding-v1',code,stage,
        'INFO' if status=='EVIDENCE_VERIFIED_ISOLATED' else 'ERROR',description)
    return VerificationDecisionV1('cog-verification-decision-v1',status,(finding,),
        evidence,request,False,False,False)

def _hash_body(domain, body):
    # Exact COG-003 _seal encoding, independently evaluated over expected values.
    return sha256(domain+json.dumps(body,sort_keys=True,ensure_ascii=False,
        separators=(',',':')).encode('utf-8')).hexdigest()

def verify_original_evidence(value: VerificationRequestV1) -> VerificationDecisionV1:
    stage='INPUT'
    try:
        require(type(value) is VerificationRequestV1,'INPUT_TYPE')
        value.__post_init__()
        if any(x is None for x in (value.state,value.plan,value.progress,value.request,value.binding,value.evidence)):
            return _decision('VERIFICATION_DEPENDENCY_UNAVAILABLE','MISSING_DEPENDENCY',
                             'INPUT','An original verification dependency is missing.')
        state,plan,progress,r,b,e=value.state,value.plan,value.progress,value.request,value.binding,value.evidence
        stage='TASK'
        state.__post_init__()
        stage='PLAN'
        plan.__post_init__()
        require(construct_plan(state,plan.steps)==plan,'ORIGINAL_PLAN')
        ready=ready_steps(plan,progress)
        stage='REQUEST'
        r.__post_init__()
        require(r.operation=='SHA256_TEXT_V1','OPERATION')
        require(r.task_id==plan.task_id and r.plan_id==plan.plan_id,'TASK_PLAN')
        require(r.progress_revision==progress.revision and r.step_id in ready,'REVISION_READY')
        raw=encoded_text(r.text)
        require(input_digest(r.text)==r.canonical_input_digest,'INPUT_DIGEST')
        req=request_commitment(r)
        prog=progress_commitment(progress)
        stage='BINDING'
        b.__post_init__()
        step=next(s for s in plan.steps if s.step_id==r.step_id)
        require((b.plan_id,b.step_id,b.symbolic_operation,b.tool_operation,b.request_digest,b.progress_digest)==
                (plan.plan_id,r.step_id,step.operation,r.operation,req,prog),'EXPLICIT_BINDING')
        binding_hash=commitment(b'SKYNET:COGToolBindingV1:v1\0',b)
        stage='EVIDENCE'
        e.__post_init__()
        stage='RECOMPUTE'
        expected_decision=dict(schema_version='cog-tool-decision-v1',request_digest=req,
            binding_digest=binding_hash,progress_digest=prog,status='ISOLATED_BINDING_VALIDATED',
            production_authorized=False)
        result=dict(schema_version='cog-tool-result-v1',request_digest=req,
            sha256_hex=sha256(raw).hexdigest(),input_byte_length=len(raw),
            status='TOOL_EXECUTED_ISOLATED',production_authorized=False)
        result['commitment']=_hash_body(b'SKYNET:COGToolResultV1:v1\0',result)
        expected=dict(schema_version='cog-tool-evidence-v1',decision=expected_decision,
            result=result,status='TOOL_EXECUTED_ISOLATED',production_authorized=False)
        expected['commitment']=_hash_body(b'SKYNET:COGToolEvidenceV1:v1\0',expected)
        from dataclasses import asdict
        require(asdict(e)==expected,'RECOMPUTATION')
        return _decision('EVIDENCE_VERIFIED_ISOLATED','VERIFIED_CONSISTENCY','COMPLETE',
                         'Original input and isolated evidence are consistent; origin is untrusted.',
                         expected['commitment'],req)
    except (ContractError,ValueError,TypeError,AttributeError,KeyError,StopIteration,RecursionError):
        _,code,description=next(row for row in TAXONOMY if row[0]==stage)
        return _decision('EVIDENCE_REJECTED',code,stage,description)
