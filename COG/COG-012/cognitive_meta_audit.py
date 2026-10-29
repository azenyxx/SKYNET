import sqlite3
from cognitive_meta_contracts import *
from cognitive_meta_policy import decide
SCHEMA="""CREATE TABLE records(sequence INTEGER PRIMARY KEY,namespace TEXT NOT NULL,trace_id TEXT NOT NULL,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,UNIQUE(namespace,trace_id));
CREATE TRIGGER immutable_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER immutable_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(db):return db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
class MetaAudit:
 @staticmethod
 def checkpoint(point):pass
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.15,isolation_level=None)
  try:
   self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(schema(self.db)==expected() and self.db.execute('PRAGMA user_version').fetchone()==(1,),'INTEGRITY_FAILURE');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',),'INTEGRITY_FAILURE');rows=self.db.execute('SELECT sequence,namespace,trace_id,body,commitment FROM records ORDER BY sequence LIMIT 1001').fetchall();require(len(rows)<=1000,'AUDIT_LIMIT');out=[];latched=set();prev='0'*64
  for seq,ns,tid,raw,h in rows:
   a=parse(MetaAuditRecordV1,raw);require(seq==len(out)+1==a.sequence and a.namespace==ns==a.trace.namespace and a.trace_id==tid==a.trace.trace_id and a.commitment==h and a.previous_commitment==prev,'INTEGRITY_FAILURE')
   require(a.decision==decide(a.trace,a.budget,stop_latched=ns in latched),'INTEGRITY_FAILURE')
   if a.decision.action=='STOP':latched.add(ns)
   out.append(a);prev=h
  return tuple(out)
 def append(self,trace,budget,expected_sequence):
  typed(expected_sequence,int)
  try:
   self.db.execute('BEGIN IMMEDIATE');old=self.verify();require(len(old)==expected_sequence and len(old)<1000,'STALE_SEQUENCE');latched=any(a.namespace==trace.namespace and a.decision.action=='STOP' for a in old);decision=decide(trace,budget,stop_latched=latched)
   a=MetaAuditRecordV1(trace.namespace,trace.trace_id,trace.timestamp,'AUDIT',(trace.commitment,),'OBSERVED','UNVERIFIED',len(old)+1,trace,budget,decision,old[-1].commitment if old else '0'*64)
   self.db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(a.sequence,a.namespace,a.trace_id,canonical(a),a.commitment));self.checkpoint('before_commit');self.db.execute('COMMIT');self.checkpoint('after_commit');return a
  except Exception as e:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(e,sqlite3.Error):raise MetaContractError('AUDIT_WRITE_REJECTED') from None
   raise
 def replay(self,namespace):
  identifier(namespace);self.db.execute('BEGIN')
  try:out=tuple(a for a in self.verify() if a.namespace==namespace);self.db.execute('COMMIT');return out
  except Exception:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   raise
