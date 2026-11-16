"""Pure validation only. Does not invoke a response provider, tools, or state transitions."""
import json
from dataclasses import fields
from hashlib import sha256
from cognitive_contracts import CognitiveStateV1, ResourcesV1, ContractError, require
from cognitive_plan_contracts import PlanStepV1
from cognitive_planner import construct_plan
from cognitive_model_planning_contracts import ModelPlanningRequestV1, ModelPlanningResponseV1, ModelPlanValidationV1


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'DUPLICATE_KEY')
        result[key] = value
    return result


def _number(_):
    raise ContractError('NUMBER')


def _keys(value, names):
    require(type(value) is dict and set(value) == set(names), 'FIELDS')


def validate_model_plan(state: CognitiveStateV1, request: ModelPlanningRequestV1,
                        response: ModelPlanningResponseV1) -> ModelPlanValidationV1:
    # Invalid typed API inputs raise ContractError; no invented binding for missing inputs.
    require(type(request) is ModelPlanningRequestV1 and type(response) is ModelPlanningResponseV1, 'INPUT_TYPE')
    request.__post_init__()
    response.__post_init__()
    binding = request.request_binding
    commitment = sha256(b'SKYNET:COGModelPlanningResponseV1:v1\0' + bytes.fromhex(binding) + response.raw_response).hexdigest()
    try:
        require(type(state) is CognitiveStateV1, 'STATE_TYPE')
        state.__post_init__()
        require((request.task_id, request.task_revision, request.objective) == (state.task.task_id, state.task.revision, state.task.objective), 'TASK_BINDING')
        require(response.request_binding == binding, 'REQUEST_BINDING')
        for f in fields(ResourcesV1):
            require(getattr(request.budget, f.name) <= getattr(state.task.budget.maximum, f.name) - getattr(state.task.budget.consumed, f.name), 'REQUEST_BUDGET')
        require(len(response.raw_response) <= request.max_response_bytes, 'OUTPUT_SIZE')
        obj = json.loads(response.raw_response.decode('utf-8'), object_pairs_hook=_pairs, parse_float=_number, parse_constant=_number)
        _keys(obj, ('schema_version', 'task_id', 'task_revision', 'steps'))
        require(obj['schema_version'] == 'cog-model-response-v1', 'SCHEMA')
        require(type(obj['task_revision']) is int and obj['task_revision'] == request.task_revision and obj['task_id'] == request.task_id, 'RESPONSE_BINDING')
        require(type(obj['steps']) is list and 1 <= len(obj['steps']) <= request.max_steps, 'STEP_COUNT')
        steps = []
        for item in obj['steps']:
            _keys(item, ('step_id', 'operation', 'dependencies', 'estimated_budget'))
            require(type(item['operation']) is str and item['operation'] in request.allowed_operations, 'OPERATION')
            require(type(item['dependencies']) is list and len(item['dependencies']) <= request.max_dependencies, 'DEPENDENCY_COUNT')
            _keys(item['estimated_budget'], (f.name for f in fields(ResourcesV1)))
            steps.append(PlanStepV1('cog-plan-step-v1', item['step_id'], item['operation'], tuple(item['dependencies']), ResourcesV1(**item['estimated_budget']), 0, 'PENDING', 0))
        # Delegate all graph validation and task feasibility to the original planner.
        plan = construct_plan(state, tuple(steps))
        for f in fields(ResourcesV1):
            require(sum(getattr(s.estimate, f.name) for s in plan.steps) <= getattr(request.budget, f.name), 'REQUEST_BUDGET_INFEASIBLE')
        return ModelPlanValidationV1('MODEL_PLAN_ACCEPTED_ISOLATED', 'ACCEPTED', plan, commitment, binding)
    except ContractError as exc:
        code = exc.code
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError, TypeError):
        code = 'MALFORMED_RESPONSE'
    return ModelPlanValidationV1('MODEL_PLAN_REJECTED', code, None, commitment, binding)
