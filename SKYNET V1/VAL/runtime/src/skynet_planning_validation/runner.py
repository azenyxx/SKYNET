import time
from .benchmark import validate,reference
from .adapter import execute
from skynet_validation.evidence import need,commitment
from skynet_validation.scoring import ratio

def score(o,expected):
 need(o['status']in('EXECUTED','UNAVAILABLE','ERROR'),'STATUS')
 if o['status']!='EXECUTED':return o['status']
 need(bool(o['calls']) and o['provenance']==commitment('val003-observed',{'calls':o['calls'],'details':o['details']}),'PROVENANCE')
 return 'PASS' if o['answer']==expected else 'FAIL'
def verify(e):
 body={k:v for k,v in e.items() if k!='digest'};need(e['digest']==commitment('val003-evidence',body),'EVIDENCE');validate(e['task']);need(e['expected']==reference(e['task']),'REFERENCE_BINDING');need(e['input_digest']==commitment('val003-input',e['task']),'INPUT_BINDING');need(e['output_digest']==commitment('val003-output',e['output']),'OUTPUT_BINDING');need(e['status']==score(e['output'],e['expected']),'SCORE');need(e['task']['track']!='native_planning' or e['status']=='UNAVAILABLE','TRACK_PROMOTION');return True

def run(tasks):
 need(type(tasks)is list and 1<=len(tasks)<=128,'COUNT');need(len({t['id'] for t in tasks})==len(tasks),'DUPLICATE');out=[];times={};absence=None
 for t in tasks:
  validate(t);start=time.monotonic_ns()
  if t['track']=='native_planning' and absence is not None:o=absence;times[t['id']]=None
  else:
   try:o=execute(t)
   except Exception as error:o={'status':'ERROR','answer':None,'calls':[],'provenance':None,'error':type(error).__name__+':'+str(error)}
   times[t['id']]=time.monotonic_ns()-start
   if t['track']=='native_planning':absence=o
  expected=reference(t);e={'task':t,'output':o,'expected':expected,'status':score(o,expected),'input_digest':commitment('val003-input',t),'output_digest':commitment('val003-output',o)};e['digest']=commitment('val003-evidence',e);out.append(e)
 return out,times

def metrics(rows):
 need(bool(rows) and len({e['task']['track'] for e in rows})==1,'TRACK_MIXING')
 for e in rows:verify(e)
 def acc(rs):return ratio(sum(e['status']=='PASS' for e in rs),len(rs))
 executed=[e for e in rows if e['status']in('PASS','FAIL','ERROR')];domains={d:[e for e in rows if e['task']['domain']==d] for d in {e['task']['domain'] for e in rows}}
 return {'track':rows[0]['task']['track'],'counts':{s:sum(e['status']==s for e in rows) for s in ('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')},'coverage':ratio(len(executed),len(rows)),'accuracy_all':acc(rows),'accuracy_executed':acc(executed),'by_domain':{d:acc(v) for d,v in sorted(domains.items())},'goal_representation_coverage':acc(domains.get('PLAN-001',[])),'dependency_validation_accuracy':acc(domains.get('PLAN-003',[])),'constraint_satisfaction':acc(domains.get('PLAN-004',[])),'execution_completion_rate':ratio(sum(e['output']['answer']['completed'] for e in domains.get('PLAN-005',[]) if e['status'] in ('PASS','FAIL')),sum(e['task']['input']['count'] for e in domains.get('PLAN-005',[]))),'failure_handling':acc([e for e in rows if e['task']['input']['kind'] in ('failure','worker_failure')]),'recovery_correctness':acc(domains.get('PLAN-006',[])),'evidence_integrity':ratio(len(rows),len(rows)),'autonomous_decomposition_accuracy':None,'autonomous_plan_revision_success':None,'goal_representation':'opaque structured payload only','dependency_constraint_execution_recovery':'See domain-specific actual observations; rejected invalid inputs can PASS validation tests but are never successful plans.'}
