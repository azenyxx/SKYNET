"""Strict isolated SHA-256 contracts. Commitments are not signatures."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict, fields
from typing import Literal, get_type_hints
from cognitive_contracts import DTO, _check, require, identifier, digest_text, ContractError, canonical_bytes

def encoded_text(text: str) -> bytes:
    require(type(text) is str and len(text)<=4096,'INPUT_TEXT')
    try:
        raw=text.encode('utf-8',errors='strict')
    except UnicodeError:
        raise ContractError('INVALID_UTF8') from None
    require(len(raw)<=4096,'INPUT_SIZE')
    return raw

def input_digest(text: str) -> str:
    encoded_text(text)
    body=json.dumps({'text':text},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(b'SKYNET:COGToolInputV1:v1\0'+body).hexdigest()

def commitment(domain: bytes, value: DTO) -> str:
    return hashlib.sha256(domain+canonical_bytes(value)).hexdigest()

def body_commitment(domain: bytes, value) -> str:
    body=asdict(value)
    del body['commitment']
    return hashlib.sha256(domain+json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

@dataclass(frozen=True)
class ToolRequestV1(DTO):
    schema_version: Literal['cog-tool-request-v1']
    task_id: str
    plan_id: str
    step_id: str
    progress_revision: int
    operation: Literal['SHA256_TEXT_V1']
    canonical_input_digest: str
    request_id: str
    text: str

    def __post_init__(self):
        # Text is arbitrary valid UTF-8 including empty/control characters; metadata is strict.
        for name,hint in get_type_hints(type(self)).items():
            if name!='text': _check(getattr(self,name),hint)
        for value in (self.task_id,self.step_id,self.request_id): identifier(value)
        digest_text(self.plan_id)
        require(self.canonical_input_digest==input_digest(self.text),'INPUT_DIGEST')

@dataclass(frozen=True)
class IsolatedToolBindingV1(DTO):
    schema_version: Literal['cog-isolated-tool-binding-v1']
    scope: Literal['ISOLATED_LOCAL_ONLY']
    plan_id: str
    step_id: str
    symbolic_operation: Literal['ANALYZE','CHECK_CONSTRAINTS','SYNTHESIZE']
    tool_operation: Literal['SHA256_TEXT_V1']
    request_digest: str
    progress_digest: str

    def __post_init__(self):
        super().__post_init__()
        identifier(self.step_id)
        for value in (self.plan_id,self.request_digest,self.progress_digest): digest_text(value)

@dataclass(frozen=True)
class ToolDecisionV1(DTO):
    schema_version: Literal['cog-tool-decision-v1']
    request_digest: str
    binding_digest: str
    progress_digest: str
    status: Literal['ISOLATED_BINDING_VALIDATED']
    production_authorized: Literal[False]

    def __post_init__(self):
        super().__post_init__()
        for value in (self.request_digest,self.binding_digest,self.progress_digest): digest_text(value)

@dataclass(frozen=True)
class ToolResultV1(DTO):
    schema_version: Literal['cog-tool-result-v1']
    request_digest: str
    sha256_hex: str
    input_byte_length: int
    status: Literal['TOOL_EXECUTED_ISOLATED']
    production_authorized: Literal[False]
    commitment: str

    def __post_init__(self):
        super().__post_init__()
        for value in (self.request_digest,self.sha256_hex,self.commitment): digest_text(value)
        require(self.input_byte_length<=4096,'RESULT_SIZE')
        require(self.commitment==body_commitment(b'SKYNET:COGToolResultV1:v1\0',self),'RESULT_COMMITMENT')

@dataclass(frozen=True)
class ToolEvidenceV1(DTO):
    schema_version: Literal['cog-tool-evidence-v1']
    decision: ToolDecisionV1
    result: ToolResultV1
    status: Literal['TOOL_EXECUTED_ISOLATED']
    production_authorized: Literal[False]
    commitment: str

    def __post_init__(self):
        super().__post_init__()
        require(self.decision.request_digest==self.result.request_digest,'EVIDENCE_BINDING')
        require(self.commitment==body_commitment(b'SKYNET:COGToolEvidenceV1:v1\0',self),'EVIDENCE_COMMITMENT')

def parse_request(raw: bytes) -> ToolRequestV1:
    require(type(raw) is bytes and len(raw)<=30000,'REQUEST_BYTES')
    def pairs(items):
        out={}
        for k,v in items:
            require(k not in out,'DUPLICATE_KEY')
            out[k]=v
        return out
    try:
        body=json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=pairs)
        require(type(body) is dict and set(body)=={f.name for f in fields(ToolRequestV1)},'FIELDS')
        result=ToolRequestV1(**body)
        require(canonical_bytes(result)==raw,'NONCANONICAL')
        return result
    except (UnicodeError,json.JSONDecodeError,RecursionError,TypeError):
        raise ContractError('MALFORMED_REQUEST') from None

def request_commitment(request):
    require(type(request) is ToolRequestV1,'REQUEST_TYPE')
    return commitment(b'SKYNET:COGToolRequestV1:v1\0',request)

def progress_commitment(progress):
    return commitment(b'SKYNET:COGToolProgressV1:v1\0',progress)
