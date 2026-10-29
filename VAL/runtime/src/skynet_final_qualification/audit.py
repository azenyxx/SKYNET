"""Read-only evidence audit; no runtime execution or historical rewriting."""
import json,hashlib,importlib
from collections import Counter
from skynet_validation.evidence import need,commitment
MODULES={1:'skynet_validation.evidence',2:'skynet_reasoning_validation.scoring',3:'skynet_planning_validation.runner',4:'skynet_memory_validation.runner',5:'skynet_adaptation_validation.validation',6:'skynet_learning_validation.validation',7:'skynet_metacognition_validation.validation',8:'skynet_autonomy_validation.validation',9:'skynet_robustness_validation.validation'}
def read(root,name):return json.loads((root/'audit'/name).read_text())
def audit(root):
 rows=[];stages=[]
 for n in range(1,10):
  name={1:'BENCHMARK-RESULTS.json',2:'REASONING-BENCHMARK-RESULTS.json'}.get(n,'VAL-%03d-EVIDENCE.json'%n);data=read(root,name);records=data if n<3 else data['first'];module=importlib.import_module(MODULES[n]);verify=getattr(module,'validate_evidence',None) or module.verify
  repeat=read(root,'BENCHMARK-REPEAT.json' if n==1 else 'REASONING-REPEAT.json') if n<3 else data['repeat'];need(len(records)==len(repeat),'REPEAT_COUNT')
  need(len({e['task'].get('id',e['task'].get('case_id')) for e in records})==len(records),'DUPLICATE')
  counts=Counter();rawhash=hashlib.sha256((root/'audit'/name).read_bytes()).hexdigest()
  for i,e in enumerate(records):
   for v in (e,repeat[i]):verify(v,data['admission']) if n>=6 else verify(v)
   status=e.get('status',e.get('execution_status'));counts[status]+=1;calls=e['output'].get('calls',[]);track=e['task'].get('track','native' if n==2 or status=='UNAVAILABLE' else 'infrastructure');native=track.startswith('native');need(not(native and status=='PASS'),'NATIVE_PROMOTION');need(status!='PASS' or bool(calls),'MISSING_INTERFACE')
   if n!=1:need(e==repeat[i],'REPEAT_MISMATCH')
   else:need({k:v for k,v in e.items() if k not in('elapsed_ns','evidence_commitment')}=={k:v for k,v in repeat[i].items() if k not in('elapsed_ns','evidence_commitment')},'REPEAT_MISMATCH')
   dg=next(e[k] for k in ('evidence_commitment','evidence_digest','digest') if k in e)
   rows.append({'id':'VAL%03d:%s'%(n,e['task'].get('id',e['task'].get('case_id'))),'stage':'VAL-%03d'%n,'capability':e['task']['domain'],'claimed_status':status,'interface':calls,'reference':'audit/'+name+('#/'+str(i) if n<3 else '#/first/'+str(i)),'file_sha256':rawhash,'evidence_digest':dg,'verification':'PASS','classification':'UNAVAILABLE' if status=='UNAVAILABLE' else ('FAILED' if status in('FAIL','ERROR') else 'INFRASTRUCTURE_ONLY' if status=='PASS' else 'NOT_MEASURED'),'provenance':'HISTORICAL_EVIDENCE','native':native,'limitations':'Local structural verification only; historical execution, not independently reproduced cognition.'})
  if n==1:report=read(root,'CAPABILITY-SCORES.json')['overall']['counts'];expected=read(root,'BENCHMARK-MANIFEST.json')['case_count']
  elif n==2:report=read(root,'REASONING-SCORES.json')['native_SKYNET']['counts'];expected=read(root,'REASONING-BENCHMARK-MANIFEST.json')['cases']
  else:
   q=read(root,'VAL-%03d-QUALIFICATION.json'%n);report=Counter()
   for s in q['scores'].values():report.update(s['counts'])
   b=read(root,'VAL-%03d-BENCHMARK.json'%n);expected=b['cases'] if n==3 else b['total']
  need(len(records)==expected and all(counts[k]==report.get(k,0) for k in set(counts)|set(report)),'COUNT_MISMATCH');stages.append({'stage':n,'records':len(records),'counts':dict(counts),'count_agreement':'PASS','repeat_integrity':'PASS','source':name,'sha256':rawhash})
 return {'records':rows,'stages':stages,'total':len(rows),'independent_authenticity':'NOT_ESTABLISHED','historical_findings':'Preserved unchanged; no closures','digest':commitment('val010-matrix',[commitment('val010-row',x) for x in rows])}
