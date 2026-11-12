import sqlite3
from dataclasses import replace
from cognitive_parallel_contracts import *
from cognitive_parallel_operators import inputs
from cognitive_parallel_verification import verify
SCHEMA="""CREATE TABLE events(seq INTEGER PRIMARY KEY,namespace TEXT NOT NULL,workload_id TEXT NOT NULL,revision INTEGER NOT NULL,action TEXT NOT NULL,body BLOB NOT NULL,commitment TEXT NOT NULL UNIQUE,previous TEXT NOT NULL,UNIQUE(namespace,workload_id,revision));
CREATE TABLE heads(namespace TEXT NOT NULL,workload_id TEXT NOT NULL,seq INTEGER NOT NULL REFERENCES events(seq),PRIMARY KEY(namespace,workload_id));
CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;"""
def schema(c):return c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
def expected_schema():
 c=sqlite3.connect(':memory:')
 try:c.executescript(SCHEMA);return schema(c)
 finally:c.close()
def genesis(w):return WorkloadSnapshotV1(w,0,tuple(TaskStateV1(t.task_id,'PENDING',0,'','') for t in w.tasks),False)
def transition(old,action,task_id='',result=None,status='FAILED'):
 require(not old.stopped,'STOP_LATCH');states=list(old.states);ids={s.task_id:i for i,s in enumerate(states)}
 if action in ('CLAIM','RESULT'):
  require(task_id in ids,'UNKNOWN_TASK');i=ids[task_id];s=states[i];t=old.workload.tasks[i]
  if action=='CLAIM':
   require(s.status=='PENDING','NOT_PENDING');require(all(states[ids[d]].status=='SUCCEEDED' for d in t.dependencies),'DEPENDENCY');require(sum(x.attempt for x in states)<old.workload.max_dispatches,'DISPATCH_BUDGET');states[i]=replace(s,status='RUNNING',attempt=1)
  else:
   require(s.status=='RUNNING','LATE_RESULT');require(status in ('SUCCEEDED','FAILED','TIMED_OUT'),'STATUS')
   if status=='SUCCEEDED':verify(t,result);states[i]=replace(s,status=status,output=result.output,result_commitment=result.commitment)
   else:require(result is None,'FAILURE_RESULT');states[i]=replace(s,status=status)
 elif action=='STOP':states=[replace(s,status='CANCELLED' if s.status=='PENDING' else 'UNKNOWN') if s.status in ('PENDING','RUNNING') else s for s in states]
 elif action=='RECOVER':states=[replace(s,status='UNKNOWN' if s.status=='RUNNING' else 'BLOCKED') if s.status in ('RUNNING','PENDING') else s for s in states]
 else:raise ParallelError('TRANSITION')
 return WorkloadSnapshotV1(old.workload,old.revision+1,tuple(states),action=='STOP')
def validate_link(old,new,action):
 new.__post_init__();[inputs(t) for t in new.workload.tasks]
 if old is None:require(action=='CREATE' and new==genesis(new.workload),'GENESIS');return
 require(old.workload==new.workload,'DEFINITION_CHANGED')
 if action in ('STOP','RECOVER'):require(new==transition(old,action),'STATE_TAMPER');return
 changed=[(a,b) for a,b in zip(old.states,new.states) if a!=b];require(len(changed)==1,'STATE_TAMPER');a,b=changed[0];t=next(t for t in old.workload.tasks if t.task_id==b.task_id);r=WorkerResultV1(t.commitment,b.attempt,b.output) if b.status=='SUCCEEDED' else None
 require(new==transition(old,action,b.task_id,r,b.status),'STATE_TAMPER')
class ParallelRegistry:
 @staticmethod
 def checkpoint(point):pass
 def __init__(self,path,initialize=False):
  self.db=sqlite3.connect(path,timeout=.3,isolation_level=None)
  try:
   self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA synchronous=FULL')
   if initialize:require(not schema(self.db),'NONEMPTY');self.db.executescript('BEGIN IMMEDIATE;'+SCHEMA+'PRAGMA user_version=1;COMMIT;')
   self.verify()
  except Exception:self.db.close();raise
 def close(self):self.db.close()
 def verify(self):
  require(schema(self.db)==expected_schema() and self.db.execute('PRAGMA user_version').fetchone()==(1,),'SCHEMA');require(self.db.execute('PRAGMA integrity_check').fetchone()==('ok',) and not self.db.execute('PRAGMA foreign_key_check').fetchall(),'INTEGRITY');rows=self.db.execute('SELECT * FROM events ORDER BY seq LIMIT 513').fetchall();require(len(rows)<=512,'EVENT_BOUND');heads={};indices={};prev='0'*64
  for seq,ns,wid,rev,action,raw,h,ph in rows:
   s=parse(WorkloadSnapshotV1,raw);key=(ns,wid);validate_link(heads.get(key),s,action);require((ns,wid,rev,h,ph)==(s.workload.namespace,s.workload.workload_id,s.revision,s.commitment,prev),'INTEGRITY');heads[key]=s;indices[key]=seq;prev=h
  actual=self.db.execute('SELECT namespace,workload_id,seq FROM heads ORDER BY namespace,workload_id').fetchall();require(actual==[(n,w,indices[n,w]) for n,w in sorted(indices)],'HEAD_INTEGRITY');return heads
 def read(self,namespace,wid):
  self.db.execute('BEGIN')
  try:h=self.verify();require((namespace,wid) in h,'WORKLOAD_MISSING');s=h[namespace,wid];self.db.execute('COMMIT');return s
  except Exception:self.db.execute('ROLLBACK');raise
 def change(self,namespace,wid,expected_revision,action,task_id='',result=None,status='FAILED',workload=None):
  typed(expected_revision,int)
  try:
   self.db.execute('BEGIN IMMEDIATE');heads=self.verify();old=heads.get((namespace,wid))
   if action=='CREATE':require(old is None and expected_revision==0 and workload.namespace==namespace and workload.workload_id==wid,'CREATE_BINDING');new=genesis(workload)
   else:require(old is not None and old.revision==expected_revision,'CAS');new=transition(old,action,task_id,result,status)
   validate_link(old,new,action);last=self.db.execute('SELECT seq,commitment FROM events ORDER BY seq DESC LIMIT 1').fetchone();seq=1 if last is None else last[0]+1;require(seq<=512,'EVENT_BOUND');self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?)',(seq,namespace,wid,new.revision,action,canonical(new),new.commitment,'0'*64 if last is None else last[1]));self.db.execute('INSERT INTO heads VALUES(?,?,?) ON CONFLICT(namespace,workload_id) DO UPDATE SET seq=excluded.seq',(namespace,wid,seq));self.checkpoint('before_commit');self.db.execute('COMMIT');self.checkpoint('after_commit');return new
  except Exception as ex:
   if self.db.in_transaction:self.db.execute('ROLLBACK')
   if isinstance(ex,sqlite3.Error):raise ParallelError('REGISTRY_ERROR') from None
   raise
