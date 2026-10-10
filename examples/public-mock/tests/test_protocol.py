import pytest
from pydantic import ValidationError
from skynet_public.protocol import MockRequest, MockResult, canonical, digest, replay, verify

def request(operation="echo", body='{"value":7}'):
    return MockRequest(schema_version="skynet-public-mock-v1", operation=operation, input_json=body, input_digest=digest(body))

def test_echo_roundtrip():
    req=request(); result=replay(req)
    assert result.output_json == req.input_json
    assert verify(req, result)

def test_noop_roundtrip():
    req=request("noop"); result=replay(req)
    assert result.output_json == "{}"
    assert verify(req, result)

def test_determinism():
    assert replay(request()) == replay(request())

def test_canonical_key_order():
    assert canonical('{"z":2,"a":1}') == '{"a":1,"z":2}'

@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":1.5}', '{"a":NaN}', '[]', 'null', '{"a":Infinity}'])
def test_invalid_json(raw):
    with pytest.raises(ValueError): canonical(raw)

@pytest.mark.parametrize("raw", ['{"value":true}', '{"value":1000001}', '{"value":-1000001}', '{"value":"7"}', '{"other":7}', '{"value":7,"extra":1}'])
def test_invalid_fixture(raw):
    with pytest.raises((ValueError,ValidationError)): request(body=raw)

def test_wrong_digest():
    with pytest.raises(ValidationError):
        MockRequest(schema_version="skynet-public-mock-v1",operation="echo",input_json='{"value":7}',input_digest='0'*64)

def test_wrong_digest_format():
    with pytest.raises(ValidationError):
        MockRequest(schema_version="skynet-public-mock-v1",operation="echo",input_json='{"value":7}',input_digest='not-a-hash')

def test_noncanonical_input():
    with pytest.raises(ValidationError): request(body='{ "value": 7 }')

def test_tampered_output():
    req=request(); result=replay(req)
    with pytest.raises(ValidationError): MockResult.model_validate({**result.model_dump(),"output_json":'{"value":8}'})

def test_forged_self_consistent_output():
    req=request(); result=replay(req)
    forged='{"value":8}'
    forged_result=MockResult.model_validate({**result.model_dump(),"output_json":forged,"output_digest":digest(forged)})
    with pytest.raises(ValueError): verify(req,forged_result)

def test_request_binding():
    a=request(); b=request(body='{"value":8}')
    with pytest.raises(ValueError): verify(b,replay(a))

def test_extra_fields_denied():
    with pytest.raises(ValidationError): MockRequest.model_validate({**request().model_dump(),"grant_id":"private"})

def test_schema_version_denied():
    with pytest.raises(ValidationError): MockRequest.model_validate({**request().model_dump(),"schema_version":"gateway-action-v1"})

def test_noncanonical_result():
    r=replay(request())
    with pytest.raises(ValidationError): MockResult.model_validate({**r.model_dump(),"output_json":'{ "value": 7 }'})
