from dataclasses import dataclass
from skynet_sys.canonical import digest,FrozenJSON,digest_text,ident
from .contracts import need,nat
@dataclass(frozen=True)
class JournalRecord:
    journal_sequence:int
    event_type:str
    subject_id:str
    logical_timestamp:int
    command:FrozenJSON
    payload_digest:str
    previous_record_hash:str
    state_digest:str
    result_code:str
    authorization_decision:str
    record_hash:str
    def body(self):return (self.journal_sequence,self.event_type,self.subject_id,self.logical_timestamp,self.payload_digest,self.previous_record_hash,self.state_digest,self.result_code,self.authorization_decision)
    def verify(self):
        nat(self.journal_sequence,0,8192);nat(self.logical_timestamp);ident(self.subject_id)
        need(type(self.command) is FrozenJSON,'JOURNAL_TAMPERED');self.command.__post_init__()
        for h in (self.payload_digest,self.previous_record_hash,self.state_digest,self.record_hash):digest_text(h)
        need(self.authorization_decision in ('ALLOW','DENY'),'JOURNAL_TAMPERED')
        need(self.payload_digest==digest('sys002-command',self.command),'JOURNAL_TAMPERED')
        need(self.record_hash==digest('sys002-journal',self.body()),'JOURNAL_TAMPERED')
def record(index,cmd,previous,state,code,decision):
    v=cmd.value();r=JournalRecord(index,v['op'],v['actor'],v['tick'],cmd,digest('sys002-command',cmd),previous,state,code,decision,'0'*64)
    from dataclasses import replace
    return replace(r,record_hash=digest('sys002-journal',r.body()))
def verify_chain(records,limit):
    need(type(records) is tuple and len(records)<=limit,'REPLAY_LIMIT');previous='0'*64
    for i,r in enumerate(records):
        need(type(r) is JournalRecord,'JOURNAL_TAMPERED');r.verify()
        need(r.journal_sequence==i and r.previous_record_hash==previous,'JOURNAL_TAMPERED');previous=r.record_hash
