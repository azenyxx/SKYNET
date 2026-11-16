import inspect,hashlib
from skynet.system import System,T
from skynet_sys.canonical import FrozenJSON,digest
from skynet_sys.evidence import EvidenceReference
from skynet_sys_recovery import Recovery,Telemetry
from skynet_sys_verification.engine import Engine,VerificationRequest,VerificationAssessment,VerificationError
from skynet_validation.registry import registry
from skynet_validation.evidence import commitment

def discover():
 objects={'Engine.evaluate':Engine.evaluate,'Recovery.collect':Recovery.collect,'Recovery.recover':Recovery.recover,'System._apply':System._apply,'registry':registry};body={'classification':'UNAVAILABLE','scope':'Exported local reference-system interfaces','sources':{k:hashlib.sha256(inspect.getsource(v).encode()).hexdigest() for k,v in objects.items()},'limits':[(r['capability_id'],r['measurement_kind'],r['limitations']) for r in registry() if r['capability_id']in('CAP-007','CAP-008','CAP-009')],'reason':'Externally submitted verdict aggregation, host telemetry and supplied recovery actions; no self-assessment confidence or autonomous correction contract.'};return dict(body,commitment=commitment('val007-admission',body))
def execute(t):
 if t['track']!='infrastructure':raise ValueError('NATIVE_INTERFACE_UNAVAILABLE')
 k=t['input']['kind'];h=System(1,1,attempts=3 if k=='retry' else 1);calls=[];details={};level='DETERMINISTIC_VERIFICATION'
 if k in ('complete','failed','retry'):
  h.run('admit');h.run('dispatch',1);lid=h.leases['t0'];answer={'initial_task':h.rows()['t0'][11],'initial_lease':h.workers.leases[lid].lease_state};before=h.state_digest()
  h.run('complete','t0') if k=='complete' else h.run('fail_worker','w0')
  if k=='retry':h.run('activate','w0');h.run('recover','RETRY','t0','host-retry');h.run('complete','t0');answer['new_attempt']=h.workers.leases[h.leases['t0']].attempt
  answer.update(task=h.rows()['t0'][11],lease=h.workers.leases[lid].lease_state);calls=['System.run.admit','System.run.dispatch','System.run.'+('complete' if k=='complete' else 'fail_worker'),'Scheduler.checkpoint'];details={'before':before,'after':h.state_digest(),'lease_id':lid};level='PROGRAMMED_ERROR_HANDLING' if k in('failed','retry') else 'EXECUTION_MONITORING'
  if k=='retry':calls+=['System.run.activate','RecoveryExecutor.RETRY','System.run.complete'];details['action_origin']='HOST_SELECTED';details['recovery_receipts']=[e.audit_commitment for e in h.coordinator.records]
 elif k in ('fixed_binding','bad_again','opposite','insufficient'):
  engine=h.engine;payload=FrozenJSON.make({'task':'t0','marker':t['input']['marker']});result=digest('worker-result-v1',payload);req=VerificationRequest('q','t0',result,'w0',('STRUCTURE','EVIDENCE'),'quorum',0);engine.open(req,payload);calls.append('Engine.open');codes=[];submitted_refs=[]
  def submit(aid,verifier,verdict,subject):
   e=EvidenceReference('e:'+aid,verifier,subject,result,'structural',T,'UNVERIFIED');submitted_refs.append(e);a=VerificationAssessment(aid,'q',verifier,verdict,(e,),('STRUCTURAL_ONLY',),0);calls.append('Engine.submit')
   try:engine.submit(a,0)
   except VerificationError as ex:codes.append(str(ex))
  submit('initial','v0','PASS','wrong-task');before=engine.state_digest()
  if k=='bad_again':submit('again','v0','PASS','still-wrong')
  else:
   submit('corrected','v0','PASS','t0')
   if k!='insufficient':submit('second','v1','FAIL' if k=='opposite' else 'PASS','t0')
  decision=engine.evaluate('q',0);calls+=['Engine.evaluate','Engine.submission_records','Engine.conflict_records'];records=engine.submission_records('q');conflicts=engine.conflict_records('q');terminal_before=engine.state_digest()
  try:engine.evaluate('q',0);terminal='ACCEPTED'
  except VerificationError as ex:terminal=str(ex)
  answer={'initial_rejection':codes[0] if codes else None,'final_verdict':decision.final_verdict,'rejected':sum(v.disposition=='REJECTED' for v in records),'accepted':sum(v.disposition=='ACCEPTED' for v in records),'conflicts':len(conflicts),'verification_status':submitted_refs[0].verification_status if len({e.verification_status for e in submitted_refs})==1 else 'MIXED','correction_origin':'HOST_SUPPLIED_REFERENCE','terminal_rejection':terminal}
  details={'before_correction_digest':before,'final_digest':engine.state_digest(),'terminal_unchanged':terminal_before==engine.state_digest(),'decision_commitment':decision.decision_commitment,'rejected_assessments':list(decision.rejected_assessments),'submissions':[v.metadata() for v in records],'conflicts':[v.metadata() for v in conflicts],'rejection_codes':codes,'payload_commitment':result}
 else:
  observer=h.observer;before=observer.state_digest();scheduler_before=h.scheduler.checkpoint('admin').commitment
  try:
   if k=='invalid_state':calls.append('Scheduler.worker_state');h.scheduler.worker_state('admin','w0','IMPOSSIBLE',0)
   elif k in ('heartbeat','stale'):
    calls.append('Recovery.collect');observer.collect('admin',Telemetry('beat','workers','HEARTBEAT','INFO',0,'trace',FrozenJSON.make({'healthy':True})))
    if k=='stale':calls.append('Recovery.heartbeat_check');fid=observer.heartbeat_check('admin','workers',2,1)
    if k=='heartbeat':answer={'health':observer.health['workers'],'faults':len(observer.faults)}
    else:f=observer.faults[fid];answer={'health':observer.health['workers'],'category':f.category,'classification':f.classification}
   else:
    event_type='UNKNOWN' if k in('invalid_event','invalid_category') else (k if k in('WORKER_FAILED','MEMORY_CONFLICT') else 'WORKER_FAILED');component='absent' if k=='unknown_component' else 'workers';value={'observed':True,'source_commitment':h.state_digest(),'marker':t['input']['marker']}
    if k=='missing_evidence':value.pop('source_commitment')
    if k=='corrupt_evidence':value['source_commitment']='forged'
    calls.append('Telemetry');event=Telemetry('fault',component,event_type,'ERROR',0,'trace',FrozenJSON.make(value));calls.append('Recovery.collect');fid=observer.collect('admin',event);f=observer.faults[fid];answer={'health':observer.health['workers'],'category':f.category,'classification':f.classification}
  except ValueError as ex:answer={'code':str(ex),'unchanged':observer.state_digest()==before and h.scheduler.checkpoint('admin').commitment==scheduler_before};details['exception_type']=type(ex).__name__
  details.update(before=before,after=observer.state_digest(),journal=[e.entry_hash for e in observer.journal],origin='HOST_TELEMETRY_OR_FIXED_VALIDATION');level='EXECUTION_MONITORING' if k in('heartbeat','stale') else 'DETERMINISTIC_VERIFICATION'
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'classification':level}
