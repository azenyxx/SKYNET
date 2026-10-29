"""Single-host in-memory reference. Methods are host control plane, not remote RPC.
No task handlers, process creation, network, persistence or independent verifier.
"""
from threading import RLock
from .canonical import ident, timestamp, digest, check
from .errors import need
from .identity import RuntimeIdentity
from .capabilities import HostPolicy, CapabilityDeclaration
from .tasks import TaskRequest, TaskResult, transition, TERMINAL
from .messages import Message
from .checkpoints import Checkpoint
from .evidence import EvidenceReference
from .audit import AuditEvent
class Runtime:
    def __init__(self,runtime_id,policy):
        ident(runtime_id);check(policy,HostPolicy)
        self.runtime_id=runtime_id;self._policy=policy;self._lock=RLock()
        self._nodes={};self._workers={};self._tasks={};self._messages={};self._checkpoints={};self._evidence={};self._keys=set();self._audit=[];self._last=None
    @property
    def audit(self):return tuple(self._audit)
    def task(self,task_id):
        ident(task_id);need(task_id in self._tasks);return self._tasks[task_id]
    def _time(self,now):
        timestamp(now);need(self._last is None or now>=self._last)
    def _capacity(self,store):need(len(store)<256)
    def _event(self,action,subject,inp,out,now):
        self._time(now);need(len(self._audit)<1024)
        i=len(self._audit)
        return AuditEvent('event:'+str(i),self.runtime_id,subject,i,action,digest('input',inp),digest('output',out),self._audit[-1].commitment if i else '0'*64,now)
    def _commit_event(self,event):self._audit.append(event);self._last=event.created_at
    def register_node(self,node,now):
        with self._lock:
            self._time(now);check(node,RuntimeIdentity);need(node.runtime_id==self.runtime_id and node.identity_type=='NODE' and node.created_at<=now)
            need(node.node_id not in self._nodes,'DUPLICATE_MESSAGE');self._capacity(self._nodes)
            e=self._event('NODE_REGISTERED',node.node_id,node,node,now);self._nodes[node.node_id]=node;self._commit_event(e)
    def register_worker(self,worker,now):
        with self._lock:
            self._time(now);check(worker,RuntimeIdentity);need(worker.runtime_id==self.runtime_id and worker.identity_type=='WORKER' and worker.node_id in self._nodes and worker.created_at<=now)
            need(worker.worker_id not in self._workers,'DUPLICATE_MESSAGE');self._capacity(self._workers)
            e=self._event('WORKER_REGISTERED',worker.worker_id,worker,worker,now);self._workers[worker.worker_id]=worker;self._commit_event(e)
    def declaration(self,worker_id):
        ident(worker_id);need(worker_id in self._workers,'INVALID_IDENTITY')
        return CapabilityDeclaration(worker_id,self._workers[worker_id].capability_set)
    def authorize(self,worker_id,cap):
        return self._policy.decide(worker_id,cap,self.declaration(worker_id).capability_set)
    def create_task(self,request,now):
        with self._lock:
            check(request,TaskRequest);self._time(now)
            need(request.created_at<=now<request.deadline,'EXPIRED_MESSAGE')
            need(request.task_id not in self._tasks and request.idempotency_key not in self._keys,'DUPLICATE_MESSAGE')
            need(request.parent_task_id is None or request.parent_task_id in self._tasks)
            self._capacity(self._tasks);decision=self.authorize(request.requester_id,request.capability_required)
            if decision.decision!='ALLOW':
                self._commit_event(self._event('CAPABILITY_DENIED',request.task_id,request,decision,now));need(False,'CAPABILITY_DENIED')
            value=(request,'CREATED',None)
            e=self._event('TASK_CREATED',request.task_id,request,value,now)
            self._tasks[request.task_id]=value;self._keys.add(request.idempotency_key);self._commit_event(e)
    def transition_task(self,task_id,new,now,result=None):
        with self._lock:
            self._time(now);req,old,prior=self.task(task_id)
            changed=transition(old,new)
            if not changed:
                need(result==prior,'INVALID_TRANSITION');return False
            need(now<req.deadline or new in ('EXPIRED','CANCELLED'),'EXPIRED_MESSAGE')
            if new=='EXPIRED':need(now>=req.deadline,'INVALID_TRANSITION')
            if result is not None:
                check(result,TaskResult)
                need(result.task_id==task_id and result.trace_id==req.trace_id and result.request_digest==req.commitment and result.producer_id==req.requester_id and result.status==new and result.created_at==now,'INVALID_TRANSITION')
            need(new in TERMINAL or result is None,'INVALID_TRANSITION')
            need(new not in ('SUCCEEDED','FAILED') or result is not None,'INVALID_TRANSITION')
            value=(req,new,result);e=self._event('TASK_TRANSITION',task_id,self._tasks[task_id],value,now)
            self._tasks[task_id]=value;self._commit_event(e);return True
    def accept_message(self,message,now):
        with self._lock:
            check(message,Message);message.validate_at(now);self._time(now)
            need(message.message_id not in self._messages,'DUPLICATE_MESSAGE');self._capacity(self._messages)
            known=set(self._nodes)|set(self._workers)|{self.runtime_id}
            need(message.producer_id in known and message.recipient_id in known,'INVALID_IDENTITY')
            need(message.causation_id is None or message.causation_id in self._messages)
            e=self._event('MESSAGE_ACCEPTED',message.message_id,message,message,now);self._messages[message.message_id]=message;self._commit_event(e)
    def checkpoint(self,checkpoint_id,task_id,now):
        with self._lock:
            ident(checkpoint_id);need(checkpoint_id not in self._checkpoints,'DUPLICATE_MESSAGE');self._capacity(self._checkpoints)
            state=self.task(task_id);old=[c for c in self._checkpoints.values() if c.task_id==task_id]
            last=old[-1] if old else None
            cp=Checkpoint(checkpoint_id,self.runtime_id,task_id,digest('task-state',state),last.sequence_number+1 if last else 0,now,last.checkpoint_id if last else None)
            e=self._event('CHECKPOINT_CREATED',task_id,state,cp,now);self._checkpoints[checkpoint_id]=cp;self._commit_event(e);return cp
    def attach_evidence(self,evidence,now):
        with self._lock:
            check(evidence,EvidenceReference);self._time(now)
            need(evidence.verification_status!='VERIFIED','EVIDENCE_UNAVAILABLE')
            need(evidence.subject_id in self._tasks and evidence.producer_id in self._workers and evidence.created_at<=now,'EVIDENCE_UNAVAILABLE')
            need(evidence.evidence_id not in self._evidence,'DUPLICATE_MESSAGE');self._capacity(self._evidence)
            e=self._event('EVIDENCE_ATTACHED',evidence.subject_id,evidence,evidence,now);self._evidence[evidence.evidence_id]=evidence;self._commit_event(e)
