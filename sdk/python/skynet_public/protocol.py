"""Standalone public research fixture API; NOT the internal Gateway wire contract."""
import hashlib
import json
from typing import Literal, Self
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Wire(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

def canonical(text: str) -> str:
    """Canonical JSON subset for public fixtures, not a general-purpose JCS implementation."""
    def unique_pairs(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError("duplicate JSON key")
            obj[k] = v
        return obj
    def reject_float(value):
        raise ValueError("non-integral JSON numbers are not supported")
    def reject_constant(value):
        raise ValueError("non-finite JSON constants are not supported")
    value = json.loads(text, object_pairs_hook=unique_pairs, parse_float=reject_float, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON object required")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(text: str) -> str:
    return hashlib.sha256(canonical(text).encode("utf-8")).hexdigest()

class MockRequest(Wire):
    schema_version: Literal["skynet-public-mock-v1"]
    operation: Literal["echo", "noop"]
    input_json: str = Field(max_length=128)
    input_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_fixture(self) -> Self:
        value = json.loads(canonical(self.input_json))
        if (self.input_json != canonical(self.input_json)
            or set(value) != {"value"}
            or type(value["value"]) is not int
            or not -1_000_000 <= value["value"] <= 1_000_000
            or digest(self.input_json) != self.input_digest):
            raise ValueError("invalid public fixture")
        return self

class MockResult(Wire):
    schema_version: Literal["skynet-public-result-v1"]
    request_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_json: str
    output_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation_kind: Literal["DETERMINISTIC_FIXTURE"]

    @model_validator(mode="after")
    def check_output_digest(self) -> Self:
        if canonical(self.output_json) != self.output_json or digest(self.output_json) != self.output_digest:
            raise ValueError("invalid output digest or canonical form")
        return self

def replay(request: MockRequest) -> MockResult:
    request = MockRequest.model_validate(request.model_dump())
    output = request.input_json if request.operation == "echo" else "{}"
    return MockResult(schema_version="skynet-public-result-v1", request_digest=digest(request.model_dump_json()), output_json=output, output_digest=digest(output), observation_kind="DETERMINISTIC_FIXTURE")

def verify(request: MockRequest, result: MockResult) -> bool:
    request = MockRequest.model_validate(request.model_dump())
    result = MockResult.model_validate(result.model_dump())
    expected = replay(request)
    if result != expected:
        raise ValueError("fixture replay mismatch")
    return True
