import sqlite3
from cognitive_rsi_contracts import *
from cognitive_rsi_baseline import validate_baseline
from cognitive_rsi_evaluation import observe
from cognitive_rsi_policy import decide
SCHEMA="""CREATE TABLE events(seq INTEGER PRIMARY KEY,namespace TEXT NOT NULL,session_id TEXT NOT NULL,proposal_id TEXT NOT NULL UNIQUE,candidate TEXT NOT NULL UNIQUE,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,previous TEXT NOT NULL,UNIQUE(namespace,session_id));
CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected_schema():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
def restore(b,before):
 validate_baseline(b);expected=digest('Sandbox',dict(baseline=b.commitment,strategy=b.strategy));require(before==expected,'ROLLBACK_MISMATCH');return ImprovementRollbackV1(b.namespace,b.session_id,(b.commitment,),'TEST_ONLY',b.commitment,before,expected,'LOCAL_SNAPSHOT_RESTORED')
def validate(s):
 require(type(s) is ImprovementSessionV1,'SESSION_TYPE');s.__post_init__();b=s.baseline;validate_baseline(b);require(all((x.namespace,x.session_id)==(s.namespace,s.session_id) for x in (b,s.observation,s.candidate,s.evaluation,s.challenge,s.decision,s.rollback)),'SCOPE');require(s.observation==observe(b),'OBSERVATION_TAMPER');require(s.candidate.proposal.bottleneck.observation_commitment==s.observation.commitment,'OBSERVATION_BINDING');require(s.rollback==restore(b,s.rollback.before_commitment),'ROLLBACK_TAMPER');require(s.decision in tuple(decide(b,s.candidate,s.evaluation,s.challenge,a) for a in ('CONTINUE','STOP','ABSTAIN')),'DECISION_TAMPER')
class ImprovementRegistry:
 @staticmethod
 def checkpoint(point):pass
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.3,isolation_level=None)
  try:
   self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(schema(self.db)==expected_schema() and self.db.execute('PRAGMA user_version').fetchone()==(1,),'SCHEMA');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',),'INTEGRITY');rows=self.db.execute('SELECT * FROM events ORDER BY seq LIMIT 101').fetchall();require(len(rows)<=100,'REGISTRY_BOUND');out=[];previous='0'*64
  for seq,ns,sid,pid,cid,body,h,prev in rows:
   s=parse(ImprovementSessionV1,body);validate(s);require(seq==len(out)+1 and (ns,sid,pid,cid,h,prev)==(s.namespace,s.session_id,s.candidate.proposal.proposal_id,s.candidate.commitment,s.commitment,previous),'INTEGRITY');out.append(s);previous=h
  return tuple(out)
 def replay(self,namespace):
  identifier(namespace);self.db.execute('BEGIN')
  try:r=tuple(s for s in self.verify() if s.namespace==namespace);self.db.execute('COMMIT');return r
  except Exception:self.db.execute('ROLLBACK');raise
 def append(self,s,expected_revision):
  validate(s);typed(expected_revision,int)
  try:
   self.db.execute('BEGIN IMMEDIATE');old=self.verify();require(len(old)==expected_revision and len(old)<100,'CAS');require(not any(x.namespace==s.namespace and x.decision.action=='STOP' for x in old),'STOP_LATCH');self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?)',(len(old)+1,s.namespace,s.session_id,s.candidate.proposal.proposal_id,s.candidate.commitment,canonical(s),s.commitment,old[-1].commitment if old else '0'*64));self.checkpoint('before_commit');self.db.execute('COMMIT');self.checkpoint('after_commit');return s
  except Exception as ex:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(ex,sqlite3.Error):raise RSIError('REGISTRY_ERROR') from None
   raise
