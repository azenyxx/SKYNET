from time import monotonic_ns
from .cases import validate
from .reference import expected as reference
from .adapter import discover,execute
from skynet_validation.evidence import need,commitment,seal
STATUSES=('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')
def check_admission(a):
 body={k:v for k,v in a.items() if k!='commitment'};need(a['commitment']==commitment('val009-admission',body) and a['classification']=='UNAVAILABLE','ADMISSION');return True
def run(cases,admission):
 check_admission(admission);need(type(cases)is list and 1<=len(cases)<=128,'BOUND');need(len({t['id'] for t in cases})==len(cases),'DUPLICATE');out=[];times={}
 for t in cases:
  validate(t)
  if t['track']=='native':o={'status':'UNAVAILABLE','answer':None,'calls':[],'details':{'admission_reference':admission['commitment'],'conditions_executed':False},'classification':'NOT_DEMONSTRATED'};times[t['id']]=None
  else:
   start=monotonic_ns()
   try:o=execute(t)
   except Exception as ex:o={'status':'ERROR','answer':None,'calls':[],'details':{'error':type(ex).__name__,'reason':str(ex)},'classification':'NOT_DEMONSTRATED'}
   times[t['id']]=monotonic_ns()-start
  expected=reference(t);status=o['status'] if o['status']!='EXECUTED' else ('PASS' if o['answer']==expected else 'FAIL')
  out.append(seal({'task':t,'status':status,'output':o,'expected':expected,'input_digest':commitment('val009-input',t),'output_digest':commitment('val009-output',o),'expected_digest':commitment('val009-expected',expected),'provenance_reference':commitment('val009-observation',{'calls':o['calls'],'details':o['details']})}))
 return out,times
def verify(e,admission):
 check_admission(admission);body={k:v for k,v in e.items() if k!='evidence_commitment'};need(e['evidence_commitment']==commitment('val001-evidence-v1',body),'EVIDENCE');t=validate(e['task']);o=e['output'];need(e['expected']==reference(t),'REFERENCE_BINDING')
 for k,d,v in [('input_digest','val009-input',t),('output_digest','val009-output',o),('expected_digest','val009-expected',e['expected'])]:need(e[k]==commitment(d,v),'BINDING')
 need(e['provenance_reference']==commitment('val009-observation',{'calls':o['calls'],'details':o['details']}),'PROVENANCE');need(e['status']in STATUSES,'STATUS')
 if t['track']=='native':need(e['status']=='UNAVAILABLE' and o['status']=='UNAVAILABLE' and not o['calls'] and o['classification']=='NOT_DEMONSTRATED' and o['details']=={'admission_reference':admission['commitment'],'conditions_executed':False},'NATIVE_PROMOTION')
 else:
  need(e['status']in('PASS','FAIL','ERROR'),'FALSE_ABSENCE');need(o['classification']=='INFRASTRUCTURE_AUTOMATION' or e['status']=='ERROR','AUTONOMY_PROMOTION')
 if e['status']in('PASS','FAIL'):need(o['status']=='EXECUTED' and bool(o['calls']),'NO_EXECUTION');need(e['status']==('PASS' if o['answer']==reference(t) else 'FAIL'),'SCORE')
 return True
def metrics(rows,admission):
 need(bool(rows) and len({e['task']['track'] for e in rows})==1,'TRACK_MIXING')
 for e in rows:verify(e,admission)
 c={k:sum(e['status']==k for e in rows) for k in STATUSES};n=len(rows);ex=sum(c[k] for k in ('PASS','FAIL','ERROR'))
 return {'total':n,'executed':ex,'counts':c,'coverage':ex/n,'accuracy_all':c['PASS']/n,'accuracy_executed':c['PASS']/ex if ex else None,**{k:'NOT_MEASURED' for k in ('native_uncertainty_performance','uncertainty_sensitive_selection')},'native_uncertainty_demonstrated':False}
