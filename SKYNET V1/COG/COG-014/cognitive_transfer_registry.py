import sqlite3
from cognitive_transfer_contracts import *
from cognitive_transfer_generalization import evaluate
from cognitive_transfer_strategy import decide
SCHEMA="""CREATE TABLE events(seq INTEGER PRIMARY KEY,namespace TEXT NOT NULL,session_id TEXT NOT NULL,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,previous TEXT NOT NULL,UNIQUE(namespace,session_id));
CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected_schema():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
def validate(s):
 require(type(s) is TransferSessionV1,'SESSION');s.__post_init__();require(s.namespace==s.source.namespace==s.target.namespace==s.evaluation.namespace==s.decision.namespace,'NAMESPACE');e=s.evaluation;require(e==evaluate(s.source,s.target,s.hypothesis,tuple(v.task for v in e.evidence),tuple(v.expected for v in e.evidence)),'EVALUATION_TAMPER');require(s.decision.provenance==(e.commitment,),'DECISION_BINDING');require(s.decision in tuple(decide(e,a,n) for a in ('CONTINUE','STOP','ABSTAIN') for n in (0,1)),'DECISION_TAMPER')
class TransferRegistry:
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.2,isolation_level=None)
  try:
   self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(schema(self.db)==expected_schema() and self.db.execute('PRAGMA user_version').fetchone()==(1,),'SCHEMA');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',),'INTEGRITY');rows=self.db.execute('SELECT * FROM events ORDER BY seq LIMIT 1001').fetchall();require(len(rows)<=1000,'REGISTRY_BOUND');out=[];prev='0'*64
  for seq,ns,sid,body,h,previous in rows:
   s=parse(TransferSessionV1,body);validate(s);require(seq==len(out)+1 and (ns,sid,h,previous)==(s.namespace,s.session_id,s.commitment,prev),'INTEGRITY');out.append(s);prev=h
  return tuple(out)
 def replay(self,namespace):
  identifier(namespace);self.db.execute('BEGIN')
  try:r=tuple(s for s in self.verify() if s.namespace==namespace);self.db.execute('COMMIT');return r
  except Exception:
   self.db.execute('ROLLBACK');raise
 def append(self,s,expected_revision):
  validate(s);typed(expected_revision,int)
  try:
   self.db.execute('BEGIN IMMEDIATE');old=self.verify();require(len(old)==expected_revision and len(old)<1000,'CAS');require(not any(x.namespace==s.namespace and x.session_id==s.session_id for x in old),'REPLAY');self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(len(old)+1,s.namespace,s.session_id,canonical(s),s.commitment,old[-1].commitment if old else '0'*64));self.db.execute('COMMIT');return s
  except Exception as ex:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(ex,sqlite3.Error):raise TransferError('REGISTRY_ERROR') from None
   raise
