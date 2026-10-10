"""Public developer helpers; fixtures only."""
import json
from .protocol import MockRequest, MockResult, canonical, digest, replay

def make_request(operation: str, value: int) -> MockRequest:
    if type(value) is not int:
        raise ValueError("value must be an integer")
    data = canonical(json.dumps({"value": value}, separators=(",", ":")))
    return MockRequest(schema_version="skynet-public-mock-v1", operation=operation, input_json=data, input_digest=digest(data))

def run(request: MockRequest) -> MockResult:
    return replay(request)

def inspect(result: MockResult) -> dict:
    checked = MockResult.model_validate(result.model_dump())
    return {"schema_version": checked.schema_version, "observation_kind": checked.observation_kind, "request_digest": checked.request_digest, "output_digest": checked.output_digest}
