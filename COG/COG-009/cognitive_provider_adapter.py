"""One synchronous local invocation. No cancellation, billing or provenance guarantee."""
from dataclasses import fields
from cognitive_contracts import CognitiveStateV1, ResourcesV1, ContractError, require
from cognitive_model_planning_contracts import ModelPlanningResponseV1
from cognitive_model_planning import validate_model_plan
from cognitive_provider_contracts import ProviderPolicyV1, ProviderRequestV1, ProviderResponseV1, ProviderInvocationResultV1, commitment, canonical


def invoke_provider(state,request,policy,transport):
    attempts=0; response_hash=None; validation_hash=None; usage=None; request_hash=None; policy_hash=None
    def result(code,plan=None):
        status='PROVIDER_PLAN_ACCEPTED_ISOLATED' if plan is not None else 'PROVIDER_REJECTED'
        trace=commitment('COGProviderTraceV1',dict(request=request_hash,policy=policy_hash,status=status,reason=code,plan_id=None if plan is None else plan.plan_id,response=response_hash,validation=validation_hash,attempts=attempts,reported_usage=usage))
        return ProviderInvocationResultV1(status,code,plan,response_hash,validation_hash,attempts,usage,trace)
    try:
        require(type(request) is ProviderRequestV1 and type(policy) is ProviderPolicyV1,'INPUT_TYPE')
        request.__post_init__(); policy.__post_init__()
        request_hash=request.request_commitment; policy_hash=commitment('COGProviderPolicyV1',policy)
        require((request.provider_id,request.model_id) in policy.allowed_provider_models,'PROVIDER_MODEL_NOT_ALLOWED')
        for name in ('max_input_bytes','max_output_bytes','max_output_tokens','max_latency_ms','max_attempts'):
            require(getattr(request,name)<=getattr(policy,name),'POLICY_LIMIT')
        require(len(canonical(request))<=request.max_input_bytes,'INPUT_SIZE')
        require(request.max_output_bytes<=request.planning_request.max_response_bytes,'PLANNING_OUTPUT_LIMIT')
        require(type(state) is CognitiveStateV1,'STATE_TYPE'); state.__post_init__()
        p=request.planning_request
        require(state.task.status=='VALIDATED','VALIDATED_TASK_REQUIRED')
        require((p.task_id,p.task_revision,p.objective)==(state.task.task_id,state.task.revision,state.task.objective),'TASK_BINDING')
        for f in fields(ResourcesV1): require(getattr(p.budget,f.name)<=getattr(state.task.budget.maximum,f.name)-getattr(state.task.budget.consumed,f.name),'REQUEST_BUDGET')
        require(callable(transport),'TRANSPORT_TYPE')
    except ContractError as exc: return result(exc.code)
    attempts=1
    try: response=transport(request)
    except Exception: return result('TRANSPORT_EXCEPTION')
    try:
        require(type(response) is ProviderResponseV1,'RESPONSE_TYPE'); response.__post_init__()
        require((response.request_id,response.provider_id,response.model_id)==(request.request_id,request.provider_id,request.model_id),'RESPONSE_BINDING')
        require(len(response.raw_output)<=request.max_output_bytes,'OUTPUT_SIZE')
        require(response.reported_output_tokens<=request.max_output_tokens,'TOKEN_LIMIT')
        require(response.reported_latency_ms<=request.max_latency_ms,'LATENCY_LIMIT')
        response_hash=response.response_commitment; usage=(response.reported_output_tokens,response.reported_latency_ms)
        validation=validate_model_plan(state,p,ModelPlanningResponseV1(response.raw_output,request.provider_id,p.request_binding))
        validation_hash=commitment('COGProviderPlanningValidationV1',validation)
        if validation.validated_plan is None: return result('COG008_'+validation.reason_code)
        return result('ACCEPTED',validation.validated_plan)
    except ContractError as exc: return result(exc.code)
