from skynet_validation.evidence import need,commitment
from .audit import audit
from skynet.system import System
CLASSES=('DEMONSTRATED','INFRASTRUCTURE_ONLY','UNAVAILABLE','NOT_MEASURED','FAILED')
GAPS=('cross_domain_reasoning','novel_problem_solving','autonomous_planning','experience_learning','unseen_transfer','independent_correction','goal_autonomy','uncertainty_adaptation')
# Explicit selection from verified historical records; never substitutes for fresh execution.
SELECT={2:[(1,'CAP-001'),(2,'R-001'),(2,'R-004'),(3,'PLAN-002'),(3,'PLAN-004'),(3,'PLAN-005'),(5,'ADAPT-004'),(5,'ADAPT-006')],3:[(4,'MEM-001'),(4,'MEM-002'),(6,'LEARN-001'),(6,'LEARN-002'),(6,'LEARN-003'),(6,'LEARN-004'),(6,'LEARN-006'),(4,'MEM-005')],4:[(7,'META-001'),(7,'META-002'),(7,'META-004'),(7,'META-003'),(7,'META-005'),(8,'AUTO-002'),(8,'AUTO-003'),(8,'AUTO-006')],5:[(9,'ROBUST-001'),(8,'AUTO-001'),(9,'ROBUST-004'),(5,'ADAPT-002'),(9,'ROBUST-005'),(9,'ROBUST-003'),(7,'META-006'),(9,'ROBUST-006')]}
def cases():return [{'id':'QUAL-%03d-%02d'%(d,i),'domain':'QUAL-%03d'%d,'index':i,'seed':(1001,2003)[i%2],'mode':'FRESH_EXECUTION' if d==1 else 'NATIVE_ADMISSION' if d==6 else 'HISTORICAL_EVIDENCE'} for d in range(1,7) for i in range(8)]
def fresh(i):
 h=System(2,2);before=h.state_digest();calls=[];facts={}
 if i==0:facts={'components':len(h.state()),'consistent':h.state_digest()==h.state_digest()};ok=all(hasattr(h,x) for x in ('runtime','bus','scheduler','memory','workers','engine','observer','recovery'));calls=['System.__init__','System.state_digest']
 elif i==1:
  h.run('admit');h.run('dispatch',2);result=h.run('complete','t0');rec=h.memory.read('admin','agent','result:t0');l=h.workers.leases[h.leases['t0']];ok=result==rec.evidence_refs[0].artifact_digest==h.workers.results[l.lease_id] and h.rows()['t0'][11]=='SUCCEEDED';facts={'result':result,'record':rec.commitment,'task':h.rows()['t0'][11]};calls=['System.admit','System.dispatch','System.complete','Store.read']
 elif i==2:
  cp=h.scheduler.checkpoint('admin').commitment
  try:h.scheduler.dispatch('intruder',0,1);code='ACCEPTED'
  except ValueError as e:code=str(e)
  ok=code=='AUTHORIZATION' and cp==h.scheduler.checkpoint('admin').commitment;facts={'code':code,'unchanged':cp==h.scheduler.checkpoint('admin').commitment};calls=['Scheduler.dispatch(intruder)']
 elif i==3:
  h.run('admit');h.run('dispatch',2);old=h.workers.leases[h.leases['t0']];h.run('recover','REQUEUE','t0','q');h.run('recover','RETRY','t0','r');h.run('complete','t0');ok=h.rows()['t0'][7]==2 and h.rows()['t0'][11]=='SUCCEEDED';facts={'attempt':h.rows()['t0'][7],'old_lease':h.workers.leases[old.lease_id].lease_state,'state':h.rows()['t0'][11]};calls=['System.admit','System.dispatch','RecoveryExecutor.REQUEUE','RecoveryExecutor.RETRY','System.complete']
 elif i==4:
  h.run('control',11,0);h.run('checkpoint','cp');h.run('control',22,1);v=h.run('restore','cp','restore');ok=v.status=='RESTORED' and v.post_state_digest==h.memory.digest();facts={'status':v.status,'memory_digest':h.memory.digest(),'restore_commitment':v.audit_commitment};calls=['System.control','Store.snapshot','System.control','Store.restore_checkpoint']
 elif i==5:
  h.run('admit');h.run('dispatch',2);h.run('complete','t0');v=h.run('verify','t0','quorum');ok=v.final_verdict=='PASS' and h.memory.read('admin','agent','result:t0').evidence_refs[0].verification_status=='UNVERIFIED';facts={'verdict':v.final_verdict,'evidence_status':'UNVERIFIED','decision':v.decision_commitment};calls=['System.admit','System.dispatch','System.complete','System.verify']
 elif i==6:
  h.run('admit');h.run('dispatch',2);original=h.state_digest();view=h.replay();ok=original==view.state_digest()==h.state_digest();facts={'replay_digest':view.state_digest(),'boundary':view.boundary,'unchanged':original==h.state_digest()};calls=['System.admit','System.dispatch','System.replay']
 else:
  try:h.run('dispatch',0);code='ACCEPTED'
  except ValueError as e:code=str(e)
  ok=code=='COMMAND_VALUE' and before==h.state_digest();facts={'code':code,'unchanged':before==h.state_digest()};calls=['System.run(dispatch,0)']
 return {'status':'PASS' if ok else 'FAIL','classification':'DEMONSTRATED' if ok else 'FAILED','capability_scope':'LOCAL_OPERATIONAL_CONTRACT','calls':calls,'before':before,'after':h.state_digest(),'facts':facts,'native_cognition':False}
def guard(row,classification,provenance=None):
 need(classification in CLASSES,'CLASSIFICATION');need(bool(row.get('reference')) and bool(row.get('evidence_digest')),'MISSING_EVIDENCE');need(row['verification']=='PASS','UNVERIFIED');need(provenance is None or provenance==row['provenance'],'HISTORICAL_AS_FRESH');need(classification==row['classification'],'FALSE_PROMOTION');return True
def level(matrix,records):
 need(len(records)==48 and len({v['case']['id'] for v in records})==48,'CASE_COUNT')
 need(matrix['total']>0 and all(x['verification']=='PASS' for x in matrix['records']),'MISSING_EVIDENCE')
 if any(v['result']['status']in('FAIL','ERROR') for v in records):return 'Q0'
 # This assessor has no independent cognition or expert-comparison evidence.
 if all(v['result']['status']=='PASS' for v in records[:8]):return 'Q1'
 return 'Q0'
def assert_level(claim,matrix,records):need(claim==level(matrix,records),'UNSUPPORTED_INTELLIGENCE_CLAIM');return True
def run(matrix):
 out=[]
 for c in cases():
  d=int(c['domain'][-3:]);i=c['index']
  if d==1:result=fresh(i)
  elif d==6:
   absent=[x for x in matrix['records'] if x['classification']=='UNAVAILABLE'];need(bool(absent),'MISSING_NATIVE_ADMISSION');result={'status':'UNAVAILABLE','classification':'UNAVAILABLE','capability':GAPS[i],'performance':'NOT_MEASURED','calls':[],'evidence_refs':[x['reference'] for x in absent if x['stage']==('VAL-002' if i<2 else 'VAL-%03d'%({2:3,3:6,4:6,5:7,6:8,7:9}[i]))][:2],'native_cognition':False}
  else:
   n,cap=SELECT[d][i];row=next(v for v in matrix['records'] if v['stage']=='VAL-%03d'%n and v['capability']==cap);guard(row,row['classification']);result={'status':'PASS','classification':row['classification'],'performance':'NOT_MEASURED' if row['classification']=='UNAVAILABLE' else 'LOCAL_DIAGNOSTIC','reference':row['reference'],'source_digest':row['evidence_digest'],'calls':['VAL010.audit.verify_historical_evidence'],'native_cognition':False,'note':'PASS means historical evidence check passed, not that the source capability exists.'}
  v={'case':c,'result':result};out.append(dict(v,commitment=commitment('val010-case',v)))
 return out
