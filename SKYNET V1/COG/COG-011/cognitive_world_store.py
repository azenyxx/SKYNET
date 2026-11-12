import sqlite3
from cognitive_world_contracts import *
from cognitive_world_transitions import empty,apply_event
SCHEMA="""CREATE TABLE events(namespace TEXT NOT NULL,revision INTEGER NOT NULL,event_id TEXT NOT NULL UNIQUE,observation_id TEXT NOT NULL UNIQUE,body BLOB NOT NULL,event_commitment TEXT NOT NULL,state_commitment TEXT NOT NULL,PRIMARY KEY(namespace,revision));
CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
class WorldStore:
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.15,isolation_level=None)
  try:
   self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(self.db.execute('PRAGMA user_version').fetchone()==(1,) and schema(self.db)==expected(),'SCHEMA');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',),'DATABASE_CORRUPT')
  states={};rows=self.db.execute('SELECT namespace,revision,event_id,observation_id,body,event_commitment,state_commitment FROM events ORDER BY namespace,revision LIMIT 4097').fetchall();require(len(rows)<=4096,'EVENT_LIMIT')
  for ns,rev,eid,oid,body,eh,sh in rows:
   e=parse(WorldEventV1,body);s=states.get(ns,empty(ns));require(e.namespace==ns and e.event_id==eid and e.observation.observation_id==oid and e.commitment==eh,'EVENT_COMMITMENT');s=apply_event(s,e);require(s.revision==rev and s.commitment==sh,'STATE_COMMITMENT');states[ns]=s
  return states
 def append(self,event):return self.append_many((event,))
 def append_many(self,events):
  require(type(events) is tuple and 1<=len(events)<=128,'BATCH_LIMIT')
  try:
   self.db.execute('BEGIN IMMEDIATE');states=self.verify();require(self.db.execute('SELECT count(*) FROM events').fetchone()[0]+len(events)<=4096,'EVENT_LIMIT')
   for e in events:
    require(type(e) is WorldEventV1,'EVENT_TYPE');require(len(canonical(e))<=8192,'EVENT_BYTES');s=apply_event(states.get(e.namespace,empty(e.namespace)),e)
    self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(e.namespace,s.revision,e.event_id,e.observation.observation_id,canonical(e),e.commitment,s.commitment));states[e.namespace]=s
   self.db.execute('COMMIT');return s
  except Exception as e:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(e,sqlite3.Error):raise WorldError('DATABASE_WRITE_REJECTED') from None
   raise
 def state(self,namespace,revision=None):
  identifier(namespace)
  if revision is not None:typed(revision,int)
  try:
   self.db.execute('BEGIN');states=self.verify();s=empty(namespace);current=states.get(namespace,s);target=current.revision if revision is None else revision;require(target<=current.revision,'REVISION_UNKNOWN')
   for body, in self.db.execute('SELECT body FROM events WHERE namespace=? AND revision<=? ORDER BY revision',(namespace,target)):s=apply_event(s,parse(WorldEventV1,body))
   self.db.execute('COMMIT');return s
  except Exception as e:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(e,sqlite3.Error):raise WorldError('DATABASE_READ_REJECTED') from None
   raise
