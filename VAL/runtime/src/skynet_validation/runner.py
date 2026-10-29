import os,sys,json,time,subprocess
from pathlib import Path
from .evidence import validate_task,commitment,seal,need
from .scoring import score

def run_case(task,expected,timeout=15):
 validate_task(task);need(type(timeout)is int and 1<=timeout<=30,'TIMEOUT');start=time.monotonic_ns()
 env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','LC_ALL')};env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]);env['PYTHONDONTWRITEBYTECODE']='1'
 try:
  proc=subprocess.run([sys.executable,'-m','skynet_validation.worker'],input=json.dumps(task),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,cwd=Path(__file__).resolve().parents[1],timeout=timeout)
  if proc.returncode:output={'status':'ERROR','answer':None,'calls':[],'provenance_reference':None,'error':proc.stderr[-12000:],'exit_code':proc.returncode}
  else:output=json.loads(proc.stdout)
 except subprocess.TimeoutExpired:output={'status':'ERROR','answer':None,'calls':[],'provenance_reference':None,'error':'TIMEOUT','exit_code':124}
 elapsed=time.monotonic_ns()-start;status=score(output,expected)
 body={'task':task,'execution_status':status,'system_interface':output.get('calls',[]),'input_digest':commitment('val001-input-v1',task),'output_digest':commitment('val001-output-v1',output),'expected_digest':commitment('val001-expected-v1',expected),'expected':expected,'output':output,'provenance_reference':output.get('provenance_reference'),'elapsed_ns':elapsed,'limitations':output.get('limitations',[])}
 return seal(body)
def run_cases(cases,max_seconds=180):
 need(type(cases)is list and 1<=len(cases)<=256,'CASE_COUNT');need(type(max_seconds)is int and 1<=max_seconds<=600,'DEADLINE');need(len({t['case_id'] for t,e in cases})==len(cases),'DUPLICATE_CASE');start=time.monotonic();results=[]
 for task,expected in cases:
  need(time.monotonic()-start<max_seconds,'DEADLINE');results.append(run_case(task,expected))
 return results
