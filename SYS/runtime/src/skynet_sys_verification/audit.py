"""Bounded lossless typed submission snapshots; integrity is not authenticity."""
from dataclasses import dataclass, fields
import json
from skynet_sys.canonical import digest, ident, digest_text
from skynet_sys.evidence import EvidenceReference

MAX_SUBMISSION_BYTES = 8192
CHUNK_SIZE = 1024

def chunks(text):
    return tuple(text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE))

def payload_digest(text):
    return digest('verification-submission-payload-v1', chunks(text))

def snapshot(assessment):
    # Imported here to avoid an engine/audit import cycle.
    from .engine import VerificationAssessment, need
    count = [0]
    def encode(value, depth=0):
        count[0] += 1
        need(depth <= 6 and count[0] <= 256, 'AUDIT_ENCODING_LIMIT')
        if value is None or type(value) is bool:
            return value
        if type(value) is int:
            need(-(2**63-1) <= value <= 2**63-1, 'AUDIT_ENCODING_LIMIT')
            return value
        if type(value) is str:
            need(len(value) <= 4096 and not any(0xD800 <= ord(c) <= 0xDFFF for c in value), 'AUDIT_ENCODING_LIMIT')
            return value
        if type(value) in (tuple, list):
            need(len(value) <= 32, 'AUDIT_ENCODING_LIMIT')
            return {'type': 'tuple' if type(value) is tuple else 'list', 'items': [encode(x, depth+1) for x in value]}
        if type(value) in (VerificationAssessment, EvidenceReference):
            return {'type': type(value).__name__, 'fields': {f.name: encode(getattr(value, f.name), depth+1) for f in fields(value)}}
        need(False, 'AUDIT_ENCODING')
    text = json.dumps(encode(assessment), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
    need(len(text.encode('ascii')) <= MAX_SUBMISSION_BYTES, 'AUDIT_PAYLOAD_SIZE')
    return text

@dataclass(frozen=True)
class SubmissionRecord:
    submission_id: str
    request_id: str
    disposition: str
    reason_code: str
    payload_json: str
    schema_version: str = 'sys006-audit-v1'

    def __post_init__(self):
        from .engine import need
        ident(self.submission_id); ident(self.request_id); ident(self.reason_code)
        need(self.disposition in ('ACCEPTED', 'REJECTED'), 'AUDIT_DISPOSITION')
        need(self.schema_version == 'sys006-audit-v1', 'AUDIT_SCHEMA')
        need(type(self.payload_json) is str and self.payload_json.isascii() and 0 < len(self.payload_json) <= MAX_SUBMISSION_BYTES, 'AUDIT_PAYLOAD_SIZE')
        # Only snapshot() creates admitted payloads; canonical JSON checked again on query.
        value = json.loads(self.payload_json)
        need(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) == self.payload_json, 'AUDIT_CANONICAL')

    @property
    def payload_commitment(self):
        return payload_digest(self.payload_json)

    @property
    def commitment(self):
        return digest('verification-submission-record-v1', (self.schema_version, self.submission_id, self.request_id, self.disposition, self.reason_code, self.payload_commitment))

    def metadata(self):
        return {'schema_version': self.schema_version, 'submission_id': self.submission_id, 'request_id': self.request_id, 'disposition': self.disposition, 'reason_code': self.reason_code, 'payload_commitment': self.payload_commitment, 'record_commitment': self.commitment, 'byte_size': len(self.payload_json), 'chunks': len(chunks(self.payload_json))}

@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    reason_code: str
    references: tuple
    schema_version: str = 'sys006-conflict-v1'

    def __post_init__(self):
        from .engine import need
        ident(self.conflict_id); ident(self.reason_code)
        need(self.schema_version == 'sys006-conflict-v1', 'AUDIT_SCHEMA')
        need(type(self.references) is tuple and 1 <= len(self.references) <= 16, 'CONFLICT_REFERENCES')
        for ref in self.references: digest_text(ref)

    @property
    def commitment(self):
        return digest('verification-conflict-record-v1', (self.schema_version, self.conflict_id, self.reason_code, self.references))

    def metadata(self):
        return {'schema_version': self.schema_version, 'conflict_id': self.conflict_id, 'reason_code': self.reason_code, 'references': self.references, 'commitment': self.commitment}
