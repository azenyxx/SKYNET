from time import monotonic_ns
from .benchmark import validate,reference
from .adapter import execute
from skynet_validation.evidence import need,commitment
STATUSES=('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')
def run(tasks):
 need(type(tasks)is list and 1<=len(tasks)<=128,'BOUND');need(len({t['id'] for t in tasks})==len(tasks),'DUPLICATE');out=[];times={}
 for t in tasks:
  validate(t);start=monotonic_ns()
  try:o=execute(t)
  except Exception as ex:o={'status':'ERROR','answer':None,'calls':[],'details':{'error':type(ex).__name__,'reason':str(ex)},'interface':'skynet_memory_validation.adapter.execute'}
  times[t['id']]=monotonic_ns()-start;expected=reference(t)
  status=o['status'] if o['status']!='EXECUTED' else ('PASS' if o['answer']==expected else 'FAIL')
  e={'case_id':t['id'],'domain':t['domain'],'track':t['track'],'seed':t['seed'],'task':t,'status':status,'execution_interface':o['interface'],'output':o,'expected':expected,'input_digest':commitment('val004-input',t),'output_digest':commitment('val004-output',o),'expected_digest':commitment('val004-expected',expected),'provenance_reference':commitment('val004-observation',{'calls':o['calls'],'details':o['details']})};e['digest']=commitment('val004-evidence',e);out.append(e)
 return out,times
def verify(e):
 body={k:v for k,v in e.items() if k!='digest'};need(e['digest']==commitment('val004-evidence',body),'EVIDENCE');t=validate(e['task']);o=e['output']
 need((e['case_id'],e['domain'],e['track'],e['seed'])==(t['id'],t['domain'],t['track'],t['seed']),'IDENTITY_BINDING');need(e['expected']==reference(t),'REFERENCE_BINDING')
 for key,domain,value in [('input_digest','val004-input',t),('output_digest','val004-output',o),('expected_digest','val004-expected',e['expected'])]:need(e[key]==commitment(domain,value),'COMMITMENT')
 need(e['provenance_reference']==commitment('val004-observation',{'calls':o['calls'],'details':o['details']}),'PROVENANCE_BINDING');need(e['status']in STATUSES,'STATUS')
 if t['track']=='infrastructure':need(e['status']in('PASS','FAIL','ERROR'),'INFRASTRUCTURE_ABSENCE')
 if t['track']=='native':need(e['status']=='UNAVAILABLE' and o['status']=='UNAVAILABLE' and not o['calls'] and o['details']['conditions_executed'] is False,'NATIVE_PROMOTION')
 if e['status']in('PASS','FAIL'):need(o['status']=='EXECUTED' and bool(o['calls']),'NO_EXECUTION');need(e['status']==('PASS' if o['answer']==reference(t) else 'FAIL'),'SCORE')
 need(e['execution_interface']==o['interface'],'INTERFACE_BINDING');return True
def metrics(rows):
 need(bool(rows) and len({r['track'] for r in rows})==1,'TRACK_MIXING')
 for r in rows:verify(r)
 c={k:sum(r['status']==k for r in rows) for k in STATUSES};n=len(rows);executed=c['PASS']+c['FAIL']+c['ERROR']
 return {'total':n,'executed':executed,'counts':c,'coverage':executed/n,'accuracy_all':c['PASS']/n,'accuracy_executed':c['PASS']/executed if executed else None,'transfer_gain':'NOT_MEASURED','learning_demonstrated':False,'persistence_after_restart':'NOT_TESTED'}
