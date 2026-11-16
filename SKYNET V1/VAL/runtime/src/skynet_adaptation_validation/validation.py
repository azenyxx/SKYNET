"""Thin VAL orchestration using inherited canonical evidence utilities."""
from time import monotonic_ns
from .benchmark import validate,reference
from .adapter import execute
from skynet_validation.evidence import need,commitment,seal
STATUSES=('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')
def run(cases):
 need(type(cases)is list and 1<=len(cases)<=128,'BOUND');need(len({t['id'] for t in cases})==len(cases),'DUPLICATE');out=[];times={}
 for t in cases:
  validate(t);start=monotonic_ns()
  try:o=execute(t)
  except Exception as e:o={'status':'ERROR','answer':None,'calls':[],'details':{'error':type(e).__name__,'reason':str(e)},'level':'NOT_DEMONSTRATED'}
  times[t['id']]=monotonic_ns()-start;expected=reference(t);status=o['status'] if o['status']!='EXECUTED' else ('PASS' if o['answer']==expected else 'FAIL')
  out.append(seal({'task':t,'status':status,'output':o,'expected':expected,'input_digest':commitment('val005-input',t),'output_digest':commitment('val005-output',o),'expected_digest':commitment('val005-expected',expected),'provenance_reference':commitment('val005-observation',{'calls':o['calls'],'details':o['details']})}))
 return out,times
def verify(e):
 b={k:v for k,v in e.items() if k!='evidence_commitment'};need(e['evidence_commitment']==commitment('val001-evidence-v1',b),'EVIDENCE');t=validate(e['task']);o=e['output'];need(e['expected']==reference(t),'REFERENCE_BINDING')
 for key,domain,value in [('input_digest','val005-input',t),('output_digest','val005-output',o),('expected_digest','val005-expected',e['expected'])]:need(e[key]==commitment(domain,value),'BINDING')
 need(e['provenance_reference']==commitment('val005-observation',{'calls':o['calls'],'details':o['details']}),'PROVENANCE');need(e['status']in STATUSES,'STATUS')
 if t['track']=='native':need(e['status']=='UNAVAILABLE' and o['status']=='UNAVAILABLE' and not o['calls'] and o['level']=='NOT_DEMONSTRATED' and o['details']['native_experiment_executed'] is False,'NATIVE_PROMOTION')
 else:
  need(e['status']in('PASS','FAIL','ERROR'),'FALSE_ABSENCE');need(o['level']in('PROGRAMMED_RESPONSE','CONSTRAINED_SELECTION','NOT_DEMONSTRATED'),'LEVEL_PROMOTION')
 if e['status']in('PASS','FAIL'):need(o['status']=='EXECUTED' and bool(o['calls']),'NO_EXECUTION');need(e['status']==('PASS' if o['answer']==reference(t) else 'FAIL'),'SCORE')
 return True
def metrics(rows):
 need(bool(rows) and len({e['task']['track'] for e in rows})==1,'TRACK_MIXING')
 for e in rows:verify(e)
 counts={k:sum(e['status']==k for e in rows) for k in STATUSES};n=len(rows);executed=sum(counts[k] for k in ('PASS','FAIL','ERROR'))
 return {'total':n,'executed':executed,'counts':counts,'coverage':executed/n,'accuracy_all':counts['PASS']/n,'accuracy_executed':counts['PASS']/executed if executed else None,'autonomous_revision_success':'NOT_MEASURED','autonomous_adaptation_demonstrated':False}
