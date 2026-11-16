from dataclasses import dataclass,replace
from copy import deepcopy
from functools import wraps
from skynet_sys.canonical import ident,digest,digest_text,FrozenJSON,check
from skynet_sys.capabilities import HostPolicy
from skynet_sys.evidence import EvidenceReference
from skynet_sys_transport.contracts import collection_digest
from .audit import SubmissionRecord, ConflictRecord, snapshot
class VerificationError(ValueError):pass
def need(ok,code):
 if not ok:raise VerificationError(code)
def number(n):need(type(n) is int and 0<=n<=1000000,'NUMBER')
def ids(v):
 need(type(v) is tuple and len(v)<=16 and all(type(x) is str for x in v) and len(set(v))==len(v),'IDENTIFIERS')
 for x in v:ident(x)
VERDICTS=('PASS','FAIL','INCONCLUSIVE','REJECTED')
@dataclass(frozen=True)
class VerificationRequest:
 request_id:str
 task_id:str
 result_commitment:str
 producer_id:str
 required_checks:tuple
 policy_id:str
 logical_tick:int
 previous_round:str|None=None
 schema_version:str='sys006-v1'
 def __post_init__(self):
  for x in (self.request_id,self.task_id,self.producer_id,self.policy_id):ident(x)
  digest_text(self.result_commitment);ids(self.required_checks);need(set(self.required_checks)=={'STRUCTURE','EVIDENCE'},'CHECKS');number(self.logical_tick);need(self.schema_version=='sys006-v1','SCHEMA')
  if self.previous_round is not None:ident(self.previous_round)
 @property
 def commitment(self):return digest('verification-request-v1',self)
@dataclass(frozen=True)
class VerificationAssessment:
 assessment_id:str
 request_id:str
 verifier_id:str
 verdict:str
 evidence_refs:tuple
 reason_codes:tuple
 logical_tick:int
 revision:int=1
 schema_version:str='sys006-v1'
 def __post_init__(self):
  for x in (self.assessment_id,self.request_id,self.verifier_id):ident(x)
  need(self.verdict in VERDICTS,'VERDICT');need(self.schema_version=='sys006-v1','SCHEMA');number(self.logical_tick);need(type(self.revision) is int and 1<=self.revision<=16,'REVISION');ids(self.reason_codes);need(bool(self.reason_codes),'REASONS');need(type(self.evidence_refs) is tuple and 1<=len(self.evidence_refs)<=4,'EVIDENCE')
  for e in self.evidence_refs:check(e,EvidenceReference)
  need(len({e.evidence_id for e in self.evidence_refs})==len(self.evidence_refs),'DUPLICATE_EVIDENCE')
 @property
 def assessment_commitment(self):return digest('verification-assessment-v1',(self.assessment_id,self.request_id,self.verifier_id,self.verdict,tuple(e.commitment for e in self.evidence_refs),self.reason_codes,self.logical_tick,self.revision,self.schema_version))
@dataclass(frozen=True)
class VerificationDecision:
 decision_id:str
 request_id:str
 policy_id:str
 final_verdict:str
 accepted_assessments:tuple
 rejected_assessments:tuple
 conflict_refs:tuple
 schema_version:str='sys006-v1'
 def __post_init__(self):
  for x in (self.decision_id,self.request_id,self.policy_id):ident(x)
  need(self.final_verdict in VERDICTS,'VERDICT');need(self.schema_version=='sys006-v1','SCHEMA');ids(self.accepted_assessments);ids(self.rejected_assessments);ids(self.conflict_refs)
 @property
 def decision_commitment(self):return digest('verification-decision-v1',self)
@dataclass(frozen=True)
class Policy:
 policy_id:str
 kind:str
 verifiers:tuple
 threshold:int=1
 max_age:int=10
 def __post_init__(self):
  ident(self.policy_id);need(self.kind in ('SINGLE_AUTHORIZED','QUORUM','UNANIMOUS'),'POLICY');ids(self.verifiers);need(1<=len(self.verifiers)<=10,'VERIFIERS');need(type(self.threshold) is int and 1<=self.threshold<=len(self.verifiers),'THRESHOLD');number(self.max_age)
  if self.kind=='SINGLE_AUTHORIZED':need(self.threshold==1 and len(self.verifiers)==1,'THRESHOLD')
@dataclass(frozen=True)
class Entry:
 sequence:int
 logical_tick:int
 operation:str
 command:tuple
 request_commitment:str
 assessment_commitment:str
 decision_commitment:str
 state_digest:str
 previous_hash:str
 entry_hash:str
 def body(self):return (self.sequence,self.logical_tick,self.operation,self.request_commitment,self.assessment_commitment,self.decision_commitment,self.state_digest,self.previous_hash)
def atomic(method):
 @wraps(method)
 def wrapper(self,*a,**kw):
  d=deepcopy(self);r=method(d,*a,**kw);self.__dict__.update(d.__dict__);return r
 return wrapper
class Engine:
 def __init__(self,authority,policies,capacity=128,*,audit_limit=32):
  check(authority,HostPolicy);need(type(policies) is tuple and 1<=len(policies)<=16,'POLICIES')
  for p in policies:need(type(p) is Policy,'POLICY');p.__post_init__()
  need(len({p.policy_id for p in policies})==len(policies),'DUPLICATE_POLICY');need(type(capacity) is int and 1<=capacity<=128,'CAPACITY');self.authority=authority;self.policies=policies;self.capacity=capacity;self.rounds={};self.journal=();self.tick=0;need(type(audit_limit) is int and 1<=audit_limit<=32,'AUDIT_LIMIT');self.audit_limit=audit_limit;self.seed=digest('verification-seed-v1',(authority.commitment,policies,capacity,audit_limit))
 def _authorize(self,a,cap):need(self.authority.decide(a,cap,(cap,)).decision=='ALLOW','UNAUTHORIZED')
 def _policy(self,k):
  p=next((x for x in self.policies if x.policy_id==k),None);need(p is not None,'UNKNOWN_POLICY');return p
 def state_digest(self):return digest('verification-state-v1',(self.seed,self.tick,collection_digest('verification-rounds-v1',tuple((k,r['request'].commitment,r['status'],tuple(sorted(a.assessment_commitment for a in r['assessments'])),tuple(sorted(r['conflicts'])),r['decision'].decision_commitment if r['decision'] else None,r['trace'],collection_digest('audit-records-v1',tuple(r['audit'])),tuple(x.commitment for x in r['submissions']),tuple(x.commitment for x in r['conflict_records'])) for k,r in sorted(self.rounds.items())))))
 def _pre(self,t):number(t);need(t>=self.tick,'CLOCK');need(len(self.journal)<1024,'JOURNAL_CAPACITY')
 def _record(self,op,cmd,t,req,a='',dec=''):
  self.tick=t;e=Entry(len(self.journal),t,op,cmd,req,a,dec,self.state_digest(),self.journal[-1].entry_hash if self.journal else self.seed,'');self.journal+=(replace(e,entry_hash=digest('verification-journal-v1',e.body())),)
 def _conflict(self,r,code,values):
  need(len(r['conflicts'])<16,'CONFLICT_CAPACITY');c='c:'+digest('verification-conflict-v1',(code,values));r['conflicts'].add(c);refs=tuple(y for x in values for y in (x if type(x) is tuple else (x,)));record=ConflictRecord(c,code,refs);r['conflict_records'].append(record);r['audit'].append(('CONFLICT',c,code,record.commitment,refs));return c
 @atomic
 def open(self,req,payload):
  need(type(req) is VerificationRequest,'REQUEST');req.__post_init__();check(payload,FrozenJSON);self._pre(req.logical_tick);self._policy(req.policy_id);self._authorize(req.producer_id,'cognitive.reason');need(digest('worker-result-v1',payload)==req.result_commitment,'RESULT_COMMITMENT');need(req.request_id not in self.rounds,'DUPLICATE_REQUEST');need(len(self.rounds)<self.capacity,'CAPACITY')
  if req.previous_round is not None:need(req.previous_round in self.rounds and self.rounds[req.previous_round]['decision'] is not None and self.rounds[req.previous_round]['request'].task_id==req.task_id,'PREVIOUS_ROUND')
  r={'request':req,'status':'OPEN','assessments':[],'conflicts':set(),'decision':None,'trace':('OPEN',),'audit':[],'submissions':[],'conflict_records':[]}
  for old in self.rounds.values():
   q=old['request']
   if q.task_id==req.task_id:
    need(req.previous_round is not None,'ROUND_LINK_REQUIRED')
    if q.result_commitment!=req.result_commitment:self._conflict(r,'TASK_RESULT_CONFLICT',(q.commitment,req.commitment))
  self.rounds[req.request_id]=r;self._record('open',(req,payload),req.logical_tick,req.commitment)
 def _submit_validated(self,a,tick):
  need(type(a) is VerificationAssessment,'ASSESSMENT');a.__post_init__();self._pre(tick);need(a.request_id in self.rounds,'UNKNOWN_REQUEST');r=self.rounds[a.request_id];need(r['decision'] is None,'TERMINAL');q=r['request'];p=self._policy(q.policy_id);need(a.verifier_id in p.verifiers and a.verifier_id!=q.producer_id,'VERIFIER');self._authorize(a.verifier_id,'cognitive.verify');need(q.logical_tick<=a.logical_tick<=tick and tick-a.logical_tick<=p.max_age,'STALE_ASSESSMENT')
  for e in a.evidence_refs:
   need(e.subject_id==q.task_id and e.artifact_digest==q.result_commitment,'EVIDENCE_BINDING');need(e.producer_id==a.verifier_id,'EVIDENCE_PRODUCER');need(e.verification_status in ('UNVERIFIED','VERIFIED'),'EVIDENCE_STATUS')
   # Original timestamp parsed by EvidenceReference; freshness explicitly pinned to assessment tick.
   from datetime import datetime,timedelta
   expected=(datetime(2026,10,25)+timedelta(seconds=a.logical_tick)).strftime('%Y-%m-%dT%H:%M:%S.%fZ');need(e.created_at==expected,'STALE_EVIDENCE')
  old=next((x for x in r['assessments'] if x.assessment_id==a.assessment_id or x.verifier_id==a.verifier_id),None)
  if old:
   need(old.assessment_commitment!=a.assessment_commitment,'DUPLICATE_ASSESSMENT');self._conflict(r,'ASSESSMENT_REVISION_CONFLICT',(old.assessment_commitment,a.assessment_commitment))
  else:
   need(len(r['assessments'])<10,'ASSESSMENT_CAPACITY')
   if any({x.verdict,a.verdict}=={'PASS','FAIL'} for x in r['assessments']):self._conflict(r,'OPPOSITE_VERDICTS',(q.commitment,tuple(sorted((x.assessment_commitment for x in r['assessments']))),a.assessment_commitment))
   r['assessments'].append(a)
  r['status']='COLLECTING';r['trace']=('OPEN','COLLECTING');return old is None
 @atomic
 def evaluate(self,rid,tick):
  self._pre(tick);need(rid in self.rounds,'UNKNOWN_REQUEST');r=self.rounds[rid];need(r['decision'] is None,'TERMINAL');p=self._policy(r['request'].policy_id);ass=sorted(r['assessments'],key=lambda a:a.assessment_id);need(all(tick-a.logical_tick<=p.max_age for a in ass),'STALE_ASSESSMENT');threshold=len(p.verifiers) if p.kind=='UNANIMOUS' else p.threshold;v={a.verdict for a in ass};verdict='INCONCLUSIVE'
  if not r['conflicts'] and len(ass)>=threshold and len(v)==1:verdict=next(iter(v))
  d=VerificationDecision('decision:'+rid,rid,p.policy_id,verdict,tuple(a.assessment_id for a in ass),tuple(x[1] for x in r['audit'] if x[0]=='REJECTED'),tuple(sorted(r['conflicts'])));r['decision']=d;r['status']='ACCEPTED' if verdict=='PASS' else ('INCONCLUSIVE' if verdict=='INCONCLUSIVE' else 'REJECTED');r['trace']=('OPEN','COLLECTING','EVALUATING',r['status']);self._record('evaluate',(rid,tick),tick,r['request'].commitment,dec=d.decision_commitment);return d
 def replay(self,entries):
  need(type(entries) is tuple and len(entries)<=1024,'JOURNAL_CAPACITY');o=Engine(self.authority,self.policies,self.capacity,audit_limit=self.audit_limit);head=self.seed
  for i,e in enumerate(entries):
   need(type(e) is Entry and e.sequence==i and e.previous_hash==head,'JOURNAL_CHAIN');need(e.entry_hash==digest('verification-journal-v1',e.body()),'JOURNAL_TAMPERED');need(e.operation in ('open','submit','evaluate'),'OPERATION');
   try:getattr(o,e.operation)(*e.command)
   except ValueError:
    need(e.operation=='submit' and len(o.journal)==i+1,'REPLAY_REJECTION')
   need(o.journal[-1]==e,'REPLAY_MISMATCH');head=e.entry_hash
  return o


 def submit(self,a,tick):
  # Admission and capacity are checked before semantic processing. Outside these
  # limits no submission is admitted and no success or rejection-record receipt exists.
  need(type(a) is VerificationAssessment,'ASSESSMENT')
  ident(a.request_id);need(a.request_id in self.rounds,'UNKNOWN_REQUEST')
  r=self.rounds[a.request_id];need(r['decision'] is None,'TERMINAL');self._pre(tick)
  need(len(r['submissions'])<self.audit_limit and sum(x.disposition=='REJECTED' for x in r['submissions'])<16 and len(r['conflicts'])<16,'AUDIT_CAPACITY')
  raw=snapshot(a);d=deepcopy(self);failure=None
  try:
   accepted=d._submit_validated(a,tick)
   reason='VALIDATED' if accepted else 'ASSESSMENT_REVISION_CONFLICT'
  except ValueError as exc:
   # Roll back any semantic work, then commit only the full diagnostic rejection.
   d=deepcopy(self);failure=exc;accepted=False;reason=str(exc)
  r=d.rounds[a.request_id]
  receipt=SubmissionRecord('submission:'+str(len(d.journal)),a.request_id,'ACCEPTED' if accepted else 'REJECTED',reason,raw)
  r['submissions'].append(receipt)
  
  try:refs=tuple(e.commitment for e in a.evidence_refs)
  except (ValueError,AttributeError,TypeError):refs=()
  r['audit'].append((receipt.disposition,receipt.submission_id,reason,receipt.commitment,refs))
  commitment=a.assessment_commitment if accepted else receipt.payload_commitment
  d._record('submit',(deepcopy(a),tick),tick,r['request'].commitment,commitment)
  self.__dict__.update(d.__dict__)
  if failure is not None:raise failure

 def audit_records(self,rid):
  need(rid in self.rounds,'UNKNOWN_REQUEST');return tuple(self.rounds[rid]['audit'])

 def submission_records(self,rid):
  need(rid in self.rounds,'UNKNOWN_REQUEST');return tuple(self.rounds[rid]['submissions'])

 def conflict_records(self,rid):
  need(rid in self.rounds,'UNKNOWN_REQUEST');return tuple(self.rounds[rid]['conflict_records'])

 def decision(self,rid):
  need(rid in self.rounds,'UNKNOWN_REQUEST');return self.rounds[rid]['decision']
