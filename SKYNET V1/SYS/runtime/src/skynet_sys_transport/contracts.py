from dataclasses import dataclass
from datetime import datetime,timedelta
import re
from skynet_sys.canonical import canonical,digest,FrozenJSON,ident,integer,timestamp,check
from skynet_sys.messages import Message,TYPES
from skynet_sys.errors import ContractError
CODES=frozenset(('INVALID_SCHEMA','UNSUPPORTED_VERSION','INVALID_IDENTITY','CAPABILITY_DENIED','INVALID_TRANSITION','DUPLICATE_MESSAGE','EXPIRED_MESSAGE','INVALID_DIGEST','EVIDENCE_UNAVAILABLE','INTERNAL_ERROR','UNKNOWN_TOPIC','QUEUE_FULL','MESSAGE_TOO_LARGE','SUBSCRIPTION_LIMIT','IDENTITY_CONFLICT','NO_SUBSCRIBERS','NOT_FOUND','WRONG_CONSUMER','STALE_ATTEMPT','DLQ_FULL','JOURNAL_FULL','HISTORY_FULL','CLOSED','CLOCK_ROLLBACK','BUSY','JOURNAL_TAMPERED','REPLAY_DIVERGENCE','REPLAY_LIMIT'))
class BusError(ValueError):
    def __init__(self,code):
        self.code=code if type(code) is str and code in CODES else 'INTERNAL_ERROR';super().__init__(self.code)
def need(ok,code='INVALID_SCHEMA'):
    if not ok:raise BusError(code)
def nat(v,low=0,high=1000000):need(type(v) is int and low<=v<=high)
def topic_name(v):need(type(v) is str and re.fullmatch(r'[a-z][a-z0-9]{0,23}\.[a-z][a-z0-9]{0,23}',v) is not None,'UNKNOWN_TOPIC')
TOPICS=('cognitive.tasks','cognitive.results','cognitive.evidence','agent.events','learning.proposals','rsi.proposals','system.audit')
OPS=('publish','subscribe','unsubscribe','poll','ack','nack','advance','inspect','replay','close')
TERMINAL=frozenset(('ACKNOWLEDGED','DEAD_LETTERED','EXPIRED'))
TRANSITIONS={'PENDING':('AVAILABLE','EXPIRED'),'AVAILABLE':('IN_FLIGHT','EXPIRED'),'IN_FLIGHT':('ACKNOWLEDGED','RETRY_PENDING','DEAD_LETTERED','EXPIRED'),'RETRY_PENDING':('AVAILABLE','EXPIRED')}
def transition(a,b):need(type(a) is str and type(b) is str and b in TRANSITIONS.get(a,()),'INVALID_TRANSITION')
@dataclass(frozen=True)
class Topic:
    name:str
    message_types:tuple
    capability:str='system.observe'
    def __post_init__(self):
        from skynet_sys.capabilities import capability
        topic_name(self.name);capability(self.capability)
        need(type(self.message_types) is tuple and 0<len(self.message_types)<=len(TYPES))
        need(all(type(x) is str and x in TYPES for x in self.message_types));need(len(set(self.message_types))==len(self.message_types))
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts:int=3
    retry_delay_ticks:int=2
    visibility_timeout_ticks:int=5
    def __post_init__(self):
        nat(self.max_attempts,1,10);nat(self.retry_delay_ticks,0,10000);nat(self.visibility_timeout_ticks,1,10000)
@dataclass(frozen=True)
class Config:
    bus_id:str='bus'
    epoch:str='2026-10-25T00:00:00.000000Z'
    queue_limit:int=256
    message_limit:int=8192
    subscription_limit:int=32
    journal_limit:int=4096
    dead_letter_limit:int=64
    history_limit:int=1024
    replay_limit:int=4096
    retry:RetryPolicy=RetryPolicy()
    schema_version:str='sys002-v1'
    def __post_init__(self):
        ident(self.bus_id);timestamp(self.epoch);need(self.schema_version=='sys002-v1','UNSUPPORTED_VERSION')
        for v,lo,hi in ((self.queue_limit,1,8192),(self.message_limit,128,12000),(self.subscription_limit,1,32),(self.journal_limit,1,8192),(self.dead_letter_limit,1,1024),(self.history_limit,1,1024),(self.replay_limit,1,8192)):nat(v,lo,hi)
        need(type(self.retry) is RetryPolicy);self.retry.__post_init__()
    def at(self,tick):
        nat(tick)
        try:return (datetime.strptime(self.epoch,'%Y-%m-%dT%H:%M:%S.%fZ')+timedelta(seconds=tick)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except (ValueError,OverflowError):raise BusError('INVALID_SCHEMA') from None
@dataclass(frozen=True)
class Subscription:
    subscription_id:str
    consumer_id:str
    topic:str
    active:bool=True
@dataclass(frozen=True)
class Delivery:
    delivery_id:str
    message_id:str
    message_digest:str
    subscription_id:str
    consumer_id:str
    topic:str
    partition:int
    sequence_number:int
    attempt_number:int
    enqueued_at:int
    visibility_deadline:int
    available_at:int
    delivery_status:str
@dataclass(frozen=True)
class DeadLetter:
    original_message_id:str
    delivery_id:str
    topic:str
    consumer_id:str
    failure_reason:str
    attempt_count:int
    journal_reference:int
@dataclass(frozen=True)
class Inspection:
    state_digest:str
    metrics:tuple
    backpressure:str
    deliveries:tuple
    dead_letters:tuple
    journal:tuple

def wire(message):
    check(message,Message);return FrozenJSON(canonical(message)).value()
def decode_message(value):
    need(type(value) is dict)
    from dataclasses import fields
    need(set(value)=={f.name for f in fields(Message)})
    args=dict(value);args['payload']=FrozenJSON.make(args['payload']);return Message(**args)
def collection_digest(domain,items):
    # Chunked Merkle representation reuses SYS-001 bounds, never raises their limits.
    hashes=[digest(domain+'-item',x) for x in items]
    chunks=[digest(domain+'-chunk',hashes[i:i+64]) for i in range(0,len(hashes),64)]
    while len(chunks)>64:chunks=[digest(domain+'-level',chunks[i:i+64]) for i in range(0,len(chunks),64)]
    return digest(domain+'-root',(len(hashes),tuple(chunks)))
