from dataclasses import dataclass
from typing import Literal
import hashlib
from cognitive_memory_contracts import DTO,canonical,parse,require,typed,identifier,digest_text,MemoryErrorV1
ParallelError=MemoryErrorV1
def digest(kind,obj):return hashlib.sha256(('SKYNET:Parallel:'+kind+':v1\0').encode()+canonical(obj)).hexdigest()
@dataclass(frozen=True)
class ParallelTaskV1(DTO):
 task_id:str;dependencies:tuple[str,...];priority:int;operation:Literal['SHA256_TEXT_V1','SUM_SQUARES_V1','CHECK_ORDER_V1'];payload:str;input_digest:str;schema:Literal['parallel-task-v1']='parallel-task-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.task_id);require(len(self.dependencies)<=16 and len(set(self.dependencies))==len(self.dependencies),'DEPENDENCIES');require(self.priority<=10,'PRIORITY');require(len(self.payload.encode('utf-8'))<=4096,'INPUT_BOUND');require(self.input_digest==digest('Input',dict(operation=self.operation,payload=self.payload)),'INPUT_DIGEST')
 @property
 def commitment(self):return digest('Task',self)
@dataclass(frozen=True)
class WorkloadV1(DTO):
 namespace:str;workload_id:str;plan_id:str;tasks:tuple[ParallelTaskV1,...];workers:int;queue_capacity:int;timeout_ms:int;max_dispatches:int;schema:Literal['parallel-workload-v1']='parallel-workload-v1'
 def __post_init__(self):
  super().__post_init__();identifier(self.namespace);identifier(self.workload_id);digest_text(self.plan_id);require(1<=self.workers<=8 and 1<=len(self.tasks)<=16,'WORKERS_OR_TASKS');require(len(self.tasks)<=self.queue_capacity<=16,'BACKPRESSURE');require(1<=self.timeout_ms<=2000 and len(self.tasks)<=self.max_dispatches<=16,'RESOURCE_BOUND');ids=tuple(t.task_id for t in self.tasks);require(ids==tuple(sorted(set(ids))),'TASK_ORDER');require(all(set(t.dependencies)<=set(ids) for t in self.tasks),'MISSING_DEPENDENCY')
 @property
 def commitment(self):return digest('Workload',self)
@dataclass(frozen=True)
class WorkerResultV1(DTO):
 task_commitment:str;attempt:int;output:str;schema:Literal['worker-result-v1']='worker-result-v1'
 def __post_init__(self):super().__post_init__();digest_text(self.task_commitment);require(self.attempt==1,'ATTEMPT')
 @property
 def commitment(self):return digest('Result',self)
@dataclass(frozen=True)
class TaskStateV1(DTO):
 task_id:str;status:Literal['PENDING','RUNNING','SUCCEEDED','FAILED','TIMED_OUT','CANCELLED','UNKNOWN','BLOCKED'];attempt:int;output:str;result_commitment:str;schema:Literal['task-state-v1']='task-state-v1'
@dataclass(frozen=True)
class WorkloadSnapshotV1(DTO):
 workload:WorkloadV1;revision:int;states:tuple[TaskStateV1,...];stopped:bool;schema:Literal['snapshot-v1']='snapshot-v1'
 @property
 def commitment(self):return digest('Snapshot',self)
@dataclass(frozen=True)
class ParallelOutcomeV1(DTO):
 workload_commitment:str;states:tuple[TaskStateV1,...];status:Literal['COMPLETE_ISOLATED','PARTIAL_FAILURE','STOPPED'];schema:Literal['outcome-v1']='outcome-v1'
 @property
 def commitment(self):return digest('Outcome',self)
 @property
 def production_authorized(self):return False
 @property
 def trusted_verification(self):return False
