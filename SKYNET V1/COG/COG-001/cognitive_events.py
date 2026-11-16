"""Deterministic diagnostic event chain; not a signature or durable audit store."""
import hashlib
import json
from dataclasses import asdict, replace
from cognitive_contracts import TaskEventV1, task_digest
DOMAIN = b'SKYNET:COGTaskEventV1:v1\0'

def event_digest(event: TaskEventV1) -> str:
    body = asdict(event)
    del body['event_digest']
    return hashlib.sha256(DOMAIN + json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

def make_event(before, after, transition, previous):
    event = TaskEventV1('cog-event-v1',before.task_id,before.revision,after.revision,before.status,after.status,transition.transition_type,transition.timestamp,task_digest(before),task_digest(after),previous,'0'*64)
    return replace(event,event_digest=event_digest(event))
