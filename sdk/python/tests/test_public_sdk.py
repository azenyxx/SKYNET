import json
import pytest
from pydantic import ValidationError
from skynet_public import MockRequest, MockResult, canonical, digest, replay, verify, make_request, run, inspect
from skynet_public.cli import main

@pytest.mark.parametrize("operation,value,output", [
    ("echo", 0, '{"value":0}'),
    ("echo", 42, '{"value":42}'),
    ("echo", -1000000, '{"value":-1000000}'),
    ("echo", 1000000, '{"value":1000000}'),
    ("noop", 0, "{}"),
    ("noop", 17, "{}"),
])
def test_roundtrip(operation, value, output):
    req = make_request(operation, value)
    result = run(req)
    assert result.output_json == output
    assert verify(req, result)
    assert inspect(result)["observation_kind"] == "DETERMINISTIC_FIXTURE"

@pytest.mark.parametrize("payload", [
    '{"a":1,"a":2}', '{"value":1.2}', '{"value":NaN}', '[]', 'null',
    '{"value":Infinity}', '{"value":-Infinity}',
])
def test_bad_canonical(payload):
    with pytest.raises(ValueError):
        canonical(payload)

@pytest.mark.parametrize("operation,value", [
    ("sum", 2), ("echo", True), ("echo", 1000001),
    ("echo", -1000001), ("noop", "3"), ("echo", None),
])
def test_invalid_request(operation, value):
    with pytest.raises((ValueError, ValidationError)):
        make_request(operation, value)

def test_tampered_result():
    req = make_request("echo", 4)
    receipt = run(req)
    with pytest.raises(ValueError):
        verify(make_request("echo", 5), receipt)
    with pytest.raises((ValueError, ValidationError)):
        MockResult.model_validate({**receipt.model_dump(), "output_digest": "0" * 64})

def test_tampered_request():
    req = make_request("echo", 4)
    with pytest.raises((ValueError, ValidationError)):
        MockRequest.model_validate({**req.model_dump(), "input_digest": "0" * 64})

def test_extra_fields_denied():
    req = make_request("noop", 3)
    with pytest.raises(ValidationError):
        MockRequest.model_validate({**req.model_dump(), "private_grant": "x"})

def test_noncanonical_input_denied():
    req = make_request("echo", 2)
    with pytest.raises((ValueError, ValidationError)):
        MockRequest.model_validate({**req.model_dump(), "input_json": '{ "value":2 }'})

def test_cli_self_test(capsys):
    assert main(["self-test"]) == 0
    assert capsys.readouterr().out.strip() == "PASS"

def test_cli_validate_run_verify_inspect(tmp_path, capsys):
    req = make_request("echo", 9)
    request_file = tmp_path / "request.json"
    receipt_file = tmp_path / "receipt.json"
    request_file.write_text(req.model_dump_json())
    assert main(["validate", str(request_file)]) == 0
    assert json.loads(capsys.readouterr().out)["valid"]
    assert main(["run", str(request_file)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    receipt_file.write_text(json.dumps(receipt))
    assert main(["verify", str(request_file), str(receipt_file)]) == 0
    assert json.loads(capsys.readouterr().out)["verified"]
    assert main(["inspect", str(receipt_file)]) == 0
    assert json.loads(capsys.readouterr().out)["observation_kind"] == "DETERMINISTIC_FIXTURE"

def test_cli_rejects_oversized_input(tmp_path):
    file = tmp_path / "huge.json"
    file.write_text("x" * 16385)
    with pytest.raises(ValueError, match="too large"):
        main(["validate", str(file)])

def test_replay_repeatable():
    req = make_request("echo", 8)
    assert replay(req) == replay(req)

def test_canonical_order():
    assert canonical('{"z":2,"a":1}') == '{"a":1,"z":2}'
    assert digest('{"a":1,"z":2}') == digest('{"z":2,"a":1}')
