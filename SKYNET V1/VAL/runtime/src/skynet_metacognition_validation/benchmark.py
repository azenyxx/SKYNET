from skynet_adaptation_validation.benchmark import generate as grid
from skynet_validation.evidence import need,ident,canonical
KINDS={1:('complete','failed','heartbeat','stale','complete','failed','retry','stale'),2:('invalid_state','missing_evidence','corrupt_evidence','invalid_event')*2,3:('uncertainty',)*8,4:('WORKER_FAILED','MEMORY_CONFLICT','invalid_category','unknown_component')*2,5:('self_correction',)*8,6:('fixed_binding','bad_again','opposite','insufficient')*2}
def generate():
 out=[]
 for j,t in enumerate(grid()):
  d=j//8+1;i=j%8;out.append({'id':t['id'].replace('ADAPT','META'),'domain':'META-%03d'%d,'seed':t['seed'],'difficulty':t['difficulty'],'track':'native' if d in(3,5) else 'infrastructure','input':{'kind':KINDS[d][i],'marker':100*d+i,'initial':'original-execution','evaluation':'native-only' if d in(3,5) else 'predefined-validation','correction_origin':'NONE' if d in(3,5) else 'HOST_IF_APPLICABLE'}})
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','seed','difficulty','track','input'},'CASE');ident(t['id']);need(t['domain']in ['META-%03d'%i for i in range(1,7)],'DOMAIN');d=int(t['domain'][-3:]);need(t['track']==('native' if d in(3,5) else 'infrastructure'),'TRACK');need(type(t['seed'])is int and t['seed']in(1001,2003),'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');x=t['input'];need(type(x)is dict and set(x)=={'kind','marker','initial','evaluation','correction_origin'},'INPUT');need(x['kind']in KINDS[d],'KIND');need(type(x['marker'])is int and 100<=x['marker']<=607,'MARKER');need(x['initial']=='original-execution' and x['evaluation']==('native-only' if d in(3,5) else 'predefined-validation') and x['correction_origin']==('NONE' if d in(3,5) else 'HOST_IF_APPLICABLE'),'CONTROL');canonical(t);return t
def reference(t):
 validate(t);k=t['input']['kind']
 if t['track']=='native':return None
 if k=='retry':return {'initial_task':'RUNNING','initial_lease':'ACTIVE','task':'SUCCEEDED','lease':'REVOKED','new_attempt':2}
 if k in ('complete','failed'):return {'initial_task':'RUNNING','initial_lease':'ACTIVE','task':'SUCCEEDED' if k=='complete' else 'FAILED','lease':'COMPLETED' if k=='complete' else 'REVOKED'}
 if k=='heartbeat':return {'health':'HEALTHY','faults':0}
 if k=='stale':return {'health':'UNHEALTHY','category':'STALE_HEARTBEAT','classification':'HOST_OBSERVED_NOT_INDEPENDENT'}
 codes={'invalid_state':'WORKER_STATE','missing_evidence':'EVIDENCE','corrupt_evidence':'INVALID_DIGEST','invalid_event':'EVENT_TYPE','invalid_category':'EVENT_TYPE','unknown_component':'UNKNOWN_COMPONENT'}
 if k in codes:return {'code':codes[k],'unchanged':True}
 if k in ('WORKER_FAILED','MEMORY_CONFLICT'):return {'health':'UNHEALTHY','category':k,'classification':'HOST_OBSERVED_NOT_INDEPENDENT'}
 return {'initial_rejection':'EVIDENCE_BINDING','final_verdict':'PASS' if k=='fixed_binding' else 'INCONCLUSIVE','rejected':2 if k=='bad_again' else 1,'accepted':0 if k=='bad_again' else (1 if k=='insufficient' else 2),'conflicts':1 if k=='opposite' else 0,'verification_status':'UNVERIFIED','correction_origin':'HOST_SUPPLIED_REFERENCE','terminal_rejection':'TERMINAL'}
