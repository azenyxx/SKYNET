import sqlite3
from contextlib import contextmanager
from cognitive_memory_contracts import *
from cognitive_memory_admission import validate_admission
SCHEMA="""CREATE TABLE revisions(id TEXT NOT NULL,revision INTEGER NOT NULL,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,PRIMARY KEY(id,revision));
CREATE TABLE heads(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,FOREIGN KEY(id,revision) REFERENCES revisions(id,revision));
CREATE TRIGGER immutable_update BEFORE UPDATE ON revisions BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER immutable_delete BEFORE DELETE ON revisions BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema_rows(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected_schema():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema_rows(c)
 finally:c.close()
class MemoryStore:
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.15,isolation_level=None);self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA synchronous=FULL')
  try:
   if initialize:
    require(not schema_rows(self.db),'DATABASE_NOT_EMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 @contextmanager
 def transaction(self):
  try:
   self.db.execute('BEGIN IMMEDIATE');yield;self.db.execute('COMMIT')
  except Exception as e:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(e,sqlite3.Error):raise MemoryErrorV1('DATABASE_FAILURE') from None
   raise
 def verify(self):
  try:
   require(self.db.execute('PRAGMA user_version').fetchone()==(1,) and schema_rows(self.db)==expected_schema(),'SCHEMA')
   require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',) and not self.db.execute('PRAGMA foreign_key_check').fetchall(),'DATABASE_INTEGRITY')
   rows=self.db.execute('SELECT id,revision,body,commitment FROM revisions ORDER BY id,revision').fetchall();require(len(rows)<=50000,'HISTORY_LIMIT');latest={}
   for mid,rev,body,h in rows:
    x=parse(MemoryRevisionV1,body);validate_admission(x.record);require(x.record.memory_id==mid and x.revision==rev and x.commitment==h,'COMMITMENT')
    old=latest.get(mid)
    if old is None:require(rev==0 and x.state=='CREATED' and x.previous_commitment=='0'*64 and x.timestamp==x.record.created_at,'INITIAL_REVISION')
    else:
     require(x.record==old.record and rev==old.revision+1 and x.previous_commitment==old.commitment and x.timestamp>=old.timestamp,'HISTORY');self.check_transition(old,x.state,x.timestamp)
    latest[mid]=x
   require(dict(self.db.execute('SELECT id,revision FROM heads'))=={k:v.revision for k,v in latest.items()},'HEAD_MISMATCH');return tuple(latest[k] for k in sorted(latest))
  except sqlite3.Error:raise MemoryErrorV1('DATABASE_INTEGRITY') from None
 @staticmethod
 def check_transition(old,state,now):
  allowed={'CREATED':('ADMITTED','REVOKED','TOMBSTONED'),'ADMITTED':('ACTIVE','REVOKED','EXPIRED','TOMBSTONED'),'ACTIVE':('SUPERSEDED','EXPIRED','REVOKED','TOMBSTONED'),'SUPERSEDED':('TOMBSTONED',),'EXPIRED':('TOMBSTONED',),'REVOKED':('TOMBSTONED',),'TOMBSTONED':()}
  require(state in allowed[old.state],'TRANSITION')
  if state in ('ADMITTED','ACTIVE'):require(now<old.record.expires_at,'EXPIRED')
  if state=='EXPIRED':require(now>=old.record.expires_at,'NOT_EXPIRED')
  if state=='TOMBSTONED':require(now>=old.record.retain_until,'RETENTION')
 def _insert(self,x):self.db.execute('INSERT INTO revisions VALUES(?,?,?,?)',(x.record.memory_id,x.revision,canonical(x),x.commitment))
 def create_many(self,records):
  require(type(records) is tuple and 1<=len(records)<=10000,'BATCH_LIMIT')
  for r in records:validate_admission(r)
  with self.transaction():
   current=self.verify();require(len(current)+len(records)<=10000,'STORE_LIMIT')
   for r in records:
    x=MemoryRevisionV1(r,0,'CREATED',r.created_at,'0'*64);self._insert(x);self.db.execute('INSERT INTO heads VALUES(?,0)',(r.memory_id,))
 def create(self,record):self.create_many((record,))
 def transition(self,mid,expected_revision,state,now):
  identifier(mid);typed(expected_revision,int);typed(now,int)
  with self.transaction():
   current={x.record.memory_id:x for x in self.verify()};require(mid in current,'NOT_FOUND');old=current[mid]
   require(old.revision==expected_revision and expected_revision<MAX,'STALE_REVISION');require(now>=old.timestamp,'TIME_REGRESSION');self.check_transition(old,state,now)
   x=MemoryRevisionV1(old.record,expected_revision+1,state,now,old.commitment);self._insert(x)
   require(self.db.execute('UPDATE heads SET revision=? WHERE id=? AND revision=?',(x.revision,mid,expected_revision)).rowcount==1,'CAS');return x
 def snapshot(self):
  self.db.execute('BEGIN')
  try:
   self.verify();out=tuple(parse(MemoryRevisionV1,r[0]) for r in self.db.execute('SELECT body FROM revisions ORDER BY id,revision'));self.db.execute('COMMIT');return out
  except Exception:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   raise
