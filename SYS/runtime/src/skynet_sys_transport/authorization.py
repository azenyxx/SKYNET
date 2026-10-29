from dataclasses import dataclass
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.capabilities import HostPolicy
from skynet_sys.canonical import check,ident,digest
from .contracts import need,OPS,topic_name
@dataclass(frozen=True)
class Authority:
    policy:HostPolicy
    identities:tuple
    rights:tuple
    def __post_init__(self):
        check(self.policy,HostPolicy);need(type(self.identities) is tuple and len(self.identities)<=32)
        for i in self.identities:check(i,RuntimeIdentity)
        need(len({i.worker_id for i in self.identities})==len(self.identities))
        need(type(self.rights) is tuple and len(self.rights)<=128)
        for row in self.rights:
            need(type(row) is tuple and len(row)==3);ident(row[0]);need(type(row[1]) is str and row[1] in OPS)
            if row[2]!='admin':topic_name(row[2])
        need(len(set(self.rights))==len(self.rights))
    def authorize(self,actor,op,scope,capability='system.observe'):
        ident(actor);need(op in OPS)
        identity=next((i for i in self.identities if i.worker_id==actor),None)
        need(identity is not None and (actor,op,scope) in self.rights,'CAPABILITY_DENIED')
        decision=self.policy.decide(actor,capability,identity.capability_set)
        need(decision.decision=='ALLOW','CAPABILITY_DENIED')
        return decision
    @property
    def commitment(self):
        from .contracts import collection_digest
        return digest('sys002-authority',(self.policy.commitment,tuple(i.commitment for i in self.identities),collection_digest('rights',self.rights)))
