from .evidence import need,validate_evidence,commitment

def score(output,expected):
 need(type(output)is dict and output.get('status')in('EXECUTED','UNAVAILABLE','NOT_TESTABLE','ERROR'),'OUTPUT_STATUS')
 if output['status']!='EXECUTED':return output['status']
 need(bool(output.get('calls')) and output.get('provenance_reference')is not None,'NO_EXECUTION')
 return 'PASS' if output['answer']==expected else 'FAIL'
def ratio(n,d):return {'numerator':n,'denominator':d,'value':n/d if d else None}
def metrics(records):
 need(type(records)is list and 0<len(records)<=256,'CASE_COUNT');need(len({r['task']['case_id'] for r in records})==len(records),'DUPLICATE_CASE')
 for r in records:validate_evidence(r)
 total=len(records);passed=sum(r['execution_status']=='PASS' for r in records);executed=sum(r['execution_status']in('PASS','FAIL','ERROR') for r in records);completed=sum(r['execution_status']in('PASS','FAIL') for r in records);unavailable=sum(r['execution_status']in('UNAVAILABLE','NOT_TESTABLE') for r in records)
 abst=[r for r in records if r['expected'] is not None and r['expected'].get('verdict')=='INCONCLUSIVE'];correct=sum(r['execution_status']=='PASS' for r in abst)
 # Paired repeated executions provide consistency; no cross-domain transfer claim.
 return dict(total=total,counts={s:sum(r['execution_status']==s for r in records) for s in ('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')},accuracy_all=ratio(passed,total),accuracy_executed=ratio(passed,executed),coverage=ratio(executed,total),completion_rate=ratio(completed,executed),abstention_accuracy=ratio(correct,len(abst)),unsupported_handling={'correctly_unavailable':unavailable,'not_a_passing_capability_score':True},transfer_gain={'value':None,'reason':'No transfer interface or qualifying control experiment'},correction_rate={'value':None,'reason':'No autonomous error-correction interface'},robustness={'value':None,'reason':'No causal paired perturbation experiment; difficulty-stratified accuracy reported separately'},consistency={'value':None,'reason':'Populated only by repeated independent execution comparison'},provenance_validity=ratio(sum(r['execution_status']in('PASS','FAIL') and bool(r['provenance_reference']) for r in records),completed),execution_cost={'elapsed_ns':sum(r['elapsed_ns'] for r in records),'api_calls':sum(len(r['output'].get('calls',[])) for r in records)},difficulty={d:ratio(sum(r['execution_status']=='PASS' and r['task']['difficulty']==d for r in records),sum(r['task']['difficulty']==d for r in records)) for d in ('basic','intermediate','advanced')})
def deterministic_record(r):return {k:v for k,v in r.items() if k not in ('elapsed_ns','evidence_commitment')}
def deterministic_digest(records):return commitment('val001-run-v1',[commitment('val001-case-v1',deterministic_record(r)) for r in records])

def paired_metrics(records):
 groups={}
 for r in records:
  d=r['task']['domain'];x=dict(r['task']['input'])
  if d in ('CAP-001','CAP-008'):x.pop('label',None)
  elif d=='CAP-007':x.pop('operation_id',None)
  else:continue
  key=commitment('val001-equivalence-v1',[d,x]);groups.setdefault(key,[]).append(r)
 pairs=[]
 for key,rows in sorted(groups.items()):
  for a,b in zip(rows,rows[1:]):
   pairs.append({'left':a['task']['case_id'],'right':b['task']['case_id'],'equivalence':'only identifier/label varies','agreement':a['output'].get('answer')==b['output'].get('answer'),'both_correct':a['execution_status']==b['execution_status']=='PASS'})
 return {'consistency':ratio(sum(p['agreement'] for p in pairs),len(pairs)),'robustness':ratio(sum(p['both_correct'] for p in pairs),len(pairs)),'pairs':pairs,'limitation':'Only nuisance identifier/label perturbations, not novel cognitive generalization.'}
