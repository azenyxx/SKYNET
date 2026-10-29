import sqlite3
from cognitive_research_contracts import *
from cognitive_research_runner import validate_domain,validate_observations,ENVIRONMENT_COMMITMENT
from cognitive_research_evaluation import evaluate
SCHEMA="""CREATE TABLE sessions(sequence INTEGER PRIMARY KEY,namespace TEXT NOT NULL,session_id TEXT NOT NULL,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,previous_commitment TEXT NOT NULL,UNIQUE(namespace,session_id));
CREATE TABLE experiments(experiment_id TEXT PRIMARY KEY,session_sequence INTEGER NOT NULL REFERENCES sessions(sequence));
CREATE TRIGGER no_update BEFORE UPDATE ON sessions BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON sessions BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
def validate_session(s):
 require(type(s) is ResearchSessionV1,'SESSION_TYPE');s.__post_init__();validate_domain(s.domain);validate_observations(s.domain,s.observations)
 require((s.namespace,s.session_id)==(s.domain.namespace,s.domain.session_id)==(s.budget.namespace,s.budget.session_id),'SCOPE')
 require(s.results==evaluate(s.domain,s.hypotheses,s.observations),'RESULT_TAMPER');require(len(s.experiments)==len(s.evidence)<=s.budget.max_experiments and s.iterations==len(s.experiments)<=s.budget.max_iterations,'BUDGET')
 require(s.observations[:len(s.domain.observations)]==s.domain.observations and len(s.observations)==len(s.domain.observations)+len(s.experiments),'OBSERVATION_HISTORY')
 for x,e,o in zip(s.experiments,s.evidence,s.observations[len(s.domain.observations):]):
  require(x.domain_commitment==s.domain.commitment and e.experiment_commitment==x.commitment and e.observation_commitment==o.commitment and e.environment_commitment==ENVIRONMENT_COMMITMENT and x.x==o.x,'EVIDENCE_BINDING')
 require(bool(s.decisions) and s.decisions[-1].action==s.terminal,'TERMINAL');require(len(canonical(s))<=65536,'SESSION_SIZE')
class Registry:
 @staticmethod
 def checkpoint(point):pass
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.15,isolation_level=None)
  try:
   self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(schema(self.db)==expected() and self.db.execute('PRAGMA user_version').fetchone()==(1,),'SCHEMA');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',) and not self.db.execute('PRAGMA foreign_key_check').fetchall(),'INTEGRITY')
  rows=self.db.execute('SELECT sequence,namespace,session_id,body,commitment,previous_commitment FROM sessions ORDER BY sequence LIMIT 1001').fetchall();require(len(rows)<=1000,'REGISTRY_LIMIT');out=[];prev='0'*64;experiments=[]
  for seq,ns,sid,raw,h,ph in rows:
   s=parse(ResearchSessionV1,raw);validate_session(s);require(seq==len(out)+1 and s.namespace==ns and s.session_id==sid and h==s.commitment and ph==prev,'INTEGRITY');out.append(s);prev=h;experiments.extend((e.experiment_id,seq) for e in s.experiments)
  require(sorted(experiments)==self.db.execute('SELECT experiment_id,session_sequence FROM experiments ORDER BY experiment_id').fetchall(),'EXPERIMENT_INTEGRITY');return tuple(out)
 def append(self,s,expected_sequence):
  validate_session(s);typed(expected_sequence,int)
  try:
   self.db.execute('BEGIN IMMEDIATE');old=self.verify();require(len(old)==expected_sequence and len(old)<1000,'STALE_SEQUENCE');seq=len(old)+1
   self.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',(seq,s.namespace,s.session_id,canonical(s),s.commitment,old[-1].commitment if old else '0'*64))
   for e in s.experiments:self.db.execute('INSERT INTO experiments VALUES(?,?)',(e.experiment_id,seq))
   self.checkpoint('before_commit');self.db.execute('COMMIT');self.checkpoint('after_commit');return s
  except Exception as e:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(e,sqlite3.Error):raise ResearchError('REGISTRY_WRITE_REJECTED') from None
   raise
 def replay(self,namespace):
  identifier(namespace);self.db.execute('BEGIN')
  try:r=tuple(s for s in self.verify() if s.namespace==namespace);self.db.execute('COMMIT');return r
  except Exception:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   raise
