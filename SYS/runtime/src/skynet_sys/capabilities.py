from dataclasses import dataclass
from .canonical import Contract, VERSION, ident
from .errors import need
CAPABILITIES=frozenset(('cognitive.reason','cognitive.verify','memory.read','memory.write','agent.execute','learning.propose','rsi.propose','system.observe'))
def capability(v):need(type(v) is str and v in CAPABILITIES,'CAPABILITY_DENIED')
def capabilities(v):
    need(type(v) is tuple and len(v)<=len(CAPABILITIES))
    for c in v:capability(c)
    need(len(set(v))==len(v))
@dataclass(frozen=True)
class CapabilityDeclaration(Contract):
    subject_id:str
    capability_set:tuple
    schema_version:str=VERSION
    def validate(self):capabilities(self.capability_set)
@dataclass(frozen=True)
class AuthorizationDecision(Contract):
    subject_id:str
    capability:str
    decision:str
    reason:str
    external_execution_authorized:bool=False
    schema_version:str=VERSION
    def validate(self):
        capability(self.capability);need(self.decision in ('ALLOW','DENY','UNAVAILABLE'))
        need(self.reason in ('HOST_PINNED_LOCAL_ONLY','DEFAULT_DENY','AUTHORITY_UNAVAILABLE'))
        need(self.external_execution_authorized is False)
@dataclass(frozen=True)
class HostPolicy(Contract):
    """Trusted host configuration, never constructed from incoming task data."""
    policy_id:str
    grants:tuple=()
    available:bool=True
    schema_version:str=VERSION
    def validate(self):
        need(type(self.available) is bool and type(self.grants) is tuple and len(self.grants)<=64)
        for g in self.grants:
            need(type(g) is tuple and len(g)==2);ident(g[0]);capability(g[1])
        need(len(set(self.grants))==len(self.grants))
    def decide(self,subject,cap,declared):
        self.__post_init__();ident(subject);capability(cap);capabilities(declared)
        status='UNAVAILABLE' if not self.available else ('ALLOW' if (subject,cap) in self.grants and cap in declared else 'DENY')
        reason={'ALLOW':'HOST_PINNED_LOCAL_ONLY','DENY':'DEFAULT_DENY','UNAVAILABLE':'AUTHORITY_UNAVAILABLE'}[status]
        return AuthorizationDecision(subject,cap,status,reason)
