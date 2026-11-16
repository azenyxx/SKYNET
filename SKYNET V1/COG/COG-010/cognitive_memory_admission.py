from cognitive_memory_contracts import *
def validate_admission(record):
 require(type(record) is MemoryRecordV1,'RECORD_TYPE');record.__post_init__()
 require(record.trust in ('UNVERIFIED','PROVISIONAL'),'VERIFICATION_AUTHORITY_UNAVAILABLE')
 require(len({e.evidence_id for e in record.evidence})==len(record.evidence),'DUPLICATE_EVIDENCE')
 for e in record.evidence:
  require(not e.revoked,'REVOKED_EVIDENCE');require(e.content_commitment==record.content_commitment,'EVIDENCE_BINDING')
 return record
# PROVISIONAL means supplied content and reference are internally consistent only.
# A fabricated matching hash cannot be distinguished from an actual observation here;
# no such record is VERIFIED or eligible for authoritative planning context.
