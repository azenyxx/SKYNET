"""One fixed local operation. No decision object is accepted as authority."""
from hashlib import sha256
from types import SimpleNamespace
from dataclasses import asdict
from cognitive_contracts import require
from cognitive_planner import construct_plan, ready_steps
from cognitive_plan_contracts import PlanV1, PlanProgressV1
from cognitive_tool_contracts import (
    ToolRequestV1, ToolDecisionV1, ToolResultV1, ToolEvidenceV1,
    IsolatedToolBindingV1, encoded_text, request_commitment, progress_commitment,
    commitment,
)
import json

def _seal(domain, values):
    return sha256(domain+json.dumps(values,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

def execute_isolated(state, plan: PlanV1, progress: PlanProgressV1,
                     request: ToolRequestV1, binding: IsolatedToolBindingV1) -> ToolEvidenceV1:
    require(type(plan) is PlanV1 and type(progress) is PlanProgressV1,'PLAN_TYPE')
    require(type(request) is ToolRequestV1,'REQUEST_TYPE')
    require(type(binding) is IsolatedToolBindingV1,'BINDING_TYPE')
    request.__post_init__()
    binding.__post_init__()
    require(construct_plan(state,plan.steps)==plan,'ORIGINAL_PLAN')
    ready=ready_steps(plan,progress)  # Revalidates exact definitions and progress invariants.
    require(request.task_id==plan.task_id and request.plan_id==plan.plan_id,'TASK_PLAN_BINDING')
    require(request.progress_revision==progress.revision,'STALE_PROGRESS')
    require(request.step_id in ready,'STEP_NOT_READY')
    step=next(s for s in plan.steps if s.step_id==request.step_id)
    req_digest=request_commitment(request)
    prog_digest=progress_commitment(progress)
    require((binding.plan_id,binding.step_id,binding.symbolic_operation,binding.tool_operation,binding.request_digest,binding.progress_digest)==
            (plan.plan_id,step.step_id,step.operation,request.operation,req_digest,prog_digest),'EXPLICIT_BINDING')
    require(request.operation=='SHA256_TEXT_V1','OPERATION')
    raw=encoded_text(request.text)
    decision=ToolDecisionV1('cog-tool-decision-v1',req_digest,
        commitment(b'SKYNET:COGToolBindingV1:v1\0',binding),prog_digest,
        'ISOLATED_BINDING_VALIDATED',False)
    values=dict(schema_version='cog-tool-result-v1',request_digest=req_digest,
                sha256_hex=sha256(raw).hexdigest(),input_byte_length=len(raw),
                status='TOOL_EXECUTED_ISOLATED',production_authorized=False)
    result=ToolResultV1(**values,commitment=_seal(b'SKYNET:COGToolResultV1:v1\0',values))
    evidence=dict(schema_version='cog-tool-evidence-v1',decision=asdict(decision),
                  result=asdict(result),status='TOOL_EXECUTED_ISOLATED',production_authorized=False)
    return ToolEvidenceV1('cog-tool-evidence-v1',decision,result,'TOOL_EXECUTED_ISOLATED',False,
                         _seal(b'SKYNET:COGToolEvidenceV1:v1\0',evidence))

def verify_evidence(state,plan,progress,request,binding,evidence) -> bool:
    require(type(evidence) is ToolEvidenceV1,'EVIDENCE_TYPE')
    evidence.__post_init__()
    require(execute_isolated(state,plan,progress,request,binding)==evidence,'EVIDENCE_MISMATCH')
    return True
