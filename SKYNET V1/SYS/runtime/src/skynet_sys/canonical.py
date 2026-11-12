"""Canonical JSON subset, NOT RFC 8785. Integer-only, bounded, UTF-8."""
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
import json, hashlib, re
from .errors import need, ContractError
MAX_BYTES=16384
MAX_DEPTH=8
MAX_ITEMS=128
VERSION='sys001-v1'
def ident(v):
    need(type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}',v) is not None,'INVALID_IDENTITY')
def digest_text(v):
    need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'INVALID_DIGEST')
def integer(v, low=0, high=2**63-1): need(type(v) is int and low<=v<=high)
def timestamp(v):
    need(type(v) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z',v) is not None)
    try: datetime.strptime(v,'%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError: raise ContractError('INVALID_SCHEMA') from None

def plain(v, depth=0, counter=None):
    if counter is None: counter=[0]
    counter[0]+=1
    need(depth<=MAX_DEPTH and counter[0]<=2048)
    if type(v) is FrozenJSON: return plain(v.value(),depth+1,counter)
    if is_dataclass(v) and not isinstance(v,type):
        return plain({f.name:getattr(v,f.name) for f in fields(v)},depth+1,counter)
    if type(v) is dict:
        need(len(v)<=MAX_ITEMS and all(type(k) is str and len(k)<=96 and not any(0xD800<=ord(c)<=0xDFFF for c in k) for k in v))
        return {k:plain(x,depth+1,counter) for k,x in v.items()}
    if type(v) in (list,tuple):
        need(len(v)<=MAX_ITEMS);return [plain(x,depth+1,counter) for x in v]
    if type(v) is str:
        need(len(v)<=4096 and not any(0xD800<=ord(c)<=0xDFFF for c in v));return v
    if type(v) is int: integer(v,-(2**63-1));return v
    if v is None or type(v) is bool:return v
    raise ContractError('INVALID_SCHEMA')
def canonical(v):
    b=json.dumps(plain(v),sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    need(len(b)<=MAX_BYTES);return b
def digest(domain,v):
    ident(domain)
    return hashlib.sha256(b'SKYNET:SYS001:v1\0'+domain.encode()+b'\0'+canonical(v)).hexdigest()
@dataclass(frozen=True)
class FrozenJSON:
    data: bytes
    def __post_init__(self):
        need(type(self.data) is bytes and len(self.data)<=MAX_BYTES)
        try: value=json.loads(self.data.decode('utf-8'))
        except (ValueError,UnicodeError,RecursionError): raise ContractError('INVALID_SCHEMA') from None
        need(canonical(value)==self.data)
    @classmethod
    def make(cls,v): return cls(canonical(v))
    def value(self):return json.loads(self.data)
class Contract:
    def __post_init__(self):
        need(type(self.schema_version) is str and self.schema_version==VERSION,'UNSUPPORTED_VERSION')
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id') or f.name=='idempotency_key':
                if v is None:need(f.name in ('parent_task_id','parent_checkpoint_id','correlation_id','causation_id'))
                else:ident(v)
            if f.name in ('created_at','deadline','expires_at'):timestamp(v)
        self.validate();canonical(self)
    def validate(self):pass
    @property
    def commitment(self):self.__post_init__();return digest(type(self).__name__,self)
def check(v,cls):need(type(v) is cls);v.__post_init__()
