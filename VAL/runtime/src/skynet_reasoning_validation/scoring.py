from .contracts import need,commitment,validate
from skynet_validation.scoring import ratio

def score(output,expected):
 need(type(output)is dict,'OUTPUT');s=output.get('status');need(s in ('UNAVAILABLE','NOT_TESTABLE','ERROR','EXECUTED'),'STATUS')
 if s!='EXECUTED':return s
 need(bool(output.get('execution_interface')) and bool(output.get('provenance_reference')),'MISSING_EXECUTION_EVIDENCE')
 return 'PASS' if output['answer']==expected['answer'] else 'FAIL'
def validate_evidence(e):
 body={k:v for k,v in e.items() if k!='evidence_digest'};need(e['evidence_digest']==commitment('val002-evidence',body),'EVIDENCE_DIGEST');need(e['input_digest']==commitment('val002-input',e['task']),'INPUT_BINDING');need(e['output_digest']==commitment('val002-output',e['output']),'OUTPUT_BINDING');need(e['reference_digest']==commitment('val002-reference',e['reference']),'REFERENCE_BINDING');need(e['status']==score(e['output'],e['reference']),'SCORE_BINDING');need(e['track']in('native_SKYNET','added_symbolic'),'TRACK');validate(e['task']);need(e['case_id']==e['task']['case_id'] and e['domain']==e['task']['domain'],'RECORD_BINDING');need(e['output']['status']!='EXECUTED','UNSUPPORTED_NATIVE_EXECUTION' if e['track']=='native_SKYNET' else 'ABSENT_TRACK_EXECUTION');return True
def metrics(rows):
 need(bool(rows) and len(rows)<=512,'COUNT');need(len({e['case_id'] for e in rows})==len(rows),'DUPLICATE');need(len({e['track'] for e in rows})==1,'TRACK_MIXING')
 for e in rows:validate_evidence(e)
 def subset(fn):return [e for e in rows if fn(e)]
 def accuracy(rs):return ratio(sum(e['status']=='PASS' for e in rs),len(rs))
 executed=subset(lambda e:e['status']in('PASS','FAIL','ERROR'));complete=subset(lambda e:e['status']in('PASS','FAIL'))
 groups={}
 for e in rows:groups.setdefault(e['task']['pair_id'],[]).append(e)
 pairs=[v for v in groups.values() if len(v)==2 and all(e['status']in('PASS','FAIL') for e in v)]
 contradictions=[e for e in complete if e['reference']['answer']=='CONTRADICTION'];non=[e for e in complete if e['reference']['answer']!='CONTRADICTION'];abst=[e for e in complete if e['reference']['answer']=='INSUFFICIENT_INFORMATION']
 dev=[e for e in complete if e['task']['partition']=='validation'];hold=[e for e in complete if e['task']['partition']=='holdout']
 return {'track':rows[0]['track'],'counts':{s:sum(e['status']==s for e in rows) for s in ('PASS','FAIL','ERROR','UNAVAILABLE','NOT_TESTABLE')},'accuracy_all':accuracy(rows),'accuracy_executed':accuracy(executed),'coverage':ratio(len(executed),len(rows)),'multistep_completion':ratio(sum(e['domain']=='R-004' for e in complete),sum(e['domain']=='R-004' for e in rows)),'contradiction_accuracy':accuracy(contradictions),'false_contradiction_rate':ratio(sum(e['output']['answer']=='CONTRADICTION' for e in non),len(non)),'abstention_accuracy':accuracy(abst),'equivalent_consistency':ratio(sum(a['output']['answer']==b['output']['answer'] for a,b in pairs),len(pairs)),'constraint_accuracy':accuracy([e for e in complete if e['domain']=='R-003']),'generalization_gap':accuracy(dev)['value']-accuracy(hold)['value'] if dev and hold else None,'provenance_validity':ratio(sum(bool(e['output'].get('provenance_reference')) for e in complete),len(complete)),'by_domain':{d:accuracy(subset(lambda e:e['domain']==d)) for d in sorted({e['domain'] for e in rows})},'by_difficulty':{d:accuracy(subset(lambda e:e['task']['difficulty']==d)) for d in ('basic','intermediate','advanced')},'limitation':'Null rates have zero executed denominators, not perfect abstention or logical consistency.'}
