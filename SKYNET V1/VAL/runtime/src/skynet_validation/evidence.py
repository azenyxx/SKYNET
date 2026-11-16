"""Strict bounded canonical evidence. Hashes are not independent authenticity."""
import hashlib,json,re
VERSION='val001-v1'
class Invalid(ValueError):pass
def need(ok,code):
 if not ok:raise Invalid(code)
def canonical(value):
 count=[0]
 def walk(x,depth=0):
  count[0]+=1;need(depth<=12 and count[0]<=12000,'BOUND')
  if x is None or type(x)is bool:return
  if type(x)is int:need(abs(x)<=2**63-1,'NUMBER');return
  if type(x)is str:need(len(x)<=16384 and not any(0xD800<=ord(c)<=0xDFFF for c in x),'STRING');return
  if type(x)in(list,tuple):
   need(len(x)<=1024,'BOUND')
   for v in x:walk(v,depth+1)
   return
  if type(x)is dict:
   need(len(x)<=128 and all(type(k)is str for k in x),'KEYS')
   for k,v in x.items():walk(k,depth+1);walk(v,depth+1)
   return
  raise Invalid('TYPE')
 walk(value);b=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode();need(len(b)<=262144,'SIZE');return b
def commitment(domain,value):return hashlib.sha256(domain.encode()+b'\0'+canonical(value)).hexdigest()
def ident(x):need(type(x)is str and re.fullmatch(r'[A-Za-z0-9:_-]{1,96}',x)is not None,'IDENTIFIER')
def hashcheck(x):need(type(x)is str and re.fullmatch('[0-9a-f]{64}',x)is not None,'DIGEST')
def validate_task(task):
 need(type(task)is dict and set(task)=={'schema','case_id','domain','seed','difficulty','partition','input'},'TASK_FIELDS')
 need(task['schema']==VERSION,'SCHEMA');ident(task['case_id']);need(task['domain'] in ['CAP-%03d'%i for i in range(1,11)],'DOMAIN')
 need(type(task['seed'])is int and 0<=task['seed']<=1000000,'SEED');need(task['difficulty'] in ('basic','intermediate','advanced'),'DIFFICULTY');need(task['partition'] in ('development','validation','holdout'),'PARTITION');need(type(task['input'])is dict,'INPUT');canonical(task);return task
def seal(record):return dict(record,evidence_commitment=commitment('val001-evidence-v1',record))
def validate_evidence(record):
 need(type(record)is dict and 'evidence_commitment'in record,'EVIDENCE');body={k:v for k,v in record.items() if k!='evidence_commitment'}
 need(commitment('val001-evidence-v1',body)==record['evidence_commitment'],'EVIDENCE_COMMITMENT')
 task=validate_task(body['task']);need(body['input_digest']==commitment('val001-input-v1',task),'INPUT_BINDING');need(body['output_digest']==commitment('val001-output-v1',body['output']),'OUTPUT_BINDING')
 need(body['execution_status'] in ('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE'),'STATUS');hashcheck(body['expected_digest']);need(type(body['elapsed_ns'])is int and body['elapsed_ns']>=0,'TIMING')
 need(body['output']['status'] in ('EXECUTED','UNAVAILABLE','NOT_TESTABLE','ERROR'),'OUTPUT_STATUS')
 if body['execution_status']in('PASS','FAIL'):
  need(body['output']['status']=='EXECUTED' and len(body['output']['calls'])>0,'NO_EXECUTION');need(body['provenance_reference']==body['output']['provenance_reference'],'PROVENANCE');hashcheck(body['provenance_reference']);need(body['provenance_reference']==commitment('val001-observation-v1',{'calls':body['output']['calls'],'details':body['output']['details']}),'PROVENANCE_BINDING')
 if body['execution_status']=='PASS':need(body['output']['answer']==body['expected'],'SCORE_BINDING')
 need(body['expected_digest']==commitment('val001-expected-v1',body['expected']),'EXPECTED_BINDING');return True
