import time
from .adapter import execute
from .reference import reference
from .contracts import commitment,validate,need
from .scoring import score

def run(tasks,track='native_SKYNET'):
 need(type(tasks)is list and 1<=len(tasks)<=512,'COUNT');need(len({t['case_id'] for t in tasks})==len(tasks),'DUPLICATE');records=[];timings={}
 for t in tasks:
  validate(t);start=time.monotonic_ns()
  # The native adapter receives input only. References are computed afterwards.
  output=execute(t,track);timings[t['case_id']]=time.monotonic_ns()-start;expected=reference(t)
  e={'case_id':t['case_id'],'domain':t['domain'],'track':track,'task':t,'output':output,'reference':expected,'status':score(output,expected),'input_digest':commitment('val002-input',t),'output_digest':commitment('val002-output',output),'reference_digest':commitment('val002-reference',expected),'execution_interface':output.get('execution_interface'),'provenance_reference':output.get('provenance_reference')};e['evidence_digest']=commitment('val002-evidence',e);records.append(e)
 return records,timings
