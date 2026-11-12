from dataclasses import dataclass
from skynet_sys.canonical import FrozenJSON,digest,ident,check,canonical
from skynet_sys_transport.contracts import collection_digest,nat
class SchedulingError(ValueError):pass
def need(ok,code):
 if not ok:raise SchedulingError(code)
TERMINAL=('SUCCEEDED','FAILED','CANCELLED','EXPIRED')
OPS=('admit','register','dispatch','complete','cancel','advance','worker_state','checkpoint','replay','recover')
@dataclass(frozen=True)
class Policy:
 grants:tuple
 max_tasks:int=128
 max_workers:int=16
 max_ready:int=128
 max_active:int=32
 max_operations:int=1024
 timeout_ticks:int=10
 aging_ticks:int=1
 def __post_init__(self):
  need(type(self.grants) is tuple and len(self.grants)<=128,'POLICY')
  for row in self.grants:need(type(row) is tuple and len(row)==2 and row[1] in OPS,'POLICY');ident(row[0])
  need(len(set(self.grants))==len(self.grants),'POLICY')
  for n,limit in ((self.max_tasks,256),(self.max_workers,32),(self.max_ready,256),(self.max_active,64),(self.max_operations,2048),(self.timeout_ticks,10000),(self.aging_ticks,1000)):nat(n,1,limit)
@dataclass(frozen=True)
class Entry:
 sequence:int
 command:FrozenJSON
 state_digest:str
 previous_hash:str
 record_hash:str
 def body(self):return (self.sequence,digest('scheduler-command',self.command),self.state_digest,self.previous_hash)
 def verify(self):need(self.record_hash==digest('scheduler-journal',self.body()),'JOURNAL_TAMPERED')
@dataclass(frozen=True)
class Snapshot:
 logical_tick:int
 scheduler_sequence:int
 tasks:tuple
 workers:tuple
 transport_digest:str
 journal_head:str
 initial_digest:str
 commitment:str
 def body(self):
  nat(self.logical_tick);nat(self.scheduler_sequence)
  need(type(self.tasks) is tuple and len(self.tasks)<=256 and type(self.workers) is tuple and len(self.workers)<=32,'CHECKPOINT')
  for x in self.tasks+self.workers:check(x,FrozenJSON)
  return (self.logical_tick,self.scheduler_sequence,collection_digest('scheduler-tasks',self.tasks),collection_digest('scheduler-workers',self.workers),self.transport_digest,self.journal_head,self.initial_digest)
 def verify(self):need(self.commitment==digest('scheduler-checkpoint',self.body()),'CHECKPOINT_TAMPERED')
