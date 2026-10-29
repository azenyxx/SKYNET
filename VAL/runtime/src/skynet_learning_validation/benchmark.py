"""Reuse prior bounded case grid; expected learning answers never enter adapter."""
from skynet_adaptation_validation.benchmark import generate as prior_grid
from skynet_validation.evidence import need,ident,canonical
KINDS={1:('record','feedback','missing','invalid_id','bad_provenance','duplicate_evidence','record','feedback'),2:('improvement',)*8,3:('rule',)*8,4:('unseen',)*8,5:('missing','bad_provenance','conflicting','retry')*2,6:('transfer',)*8}
def generate():
 out=[]
 for j,base in enumerate(prior_grid()):
  d=j//8+1;i=j%8;k=KINDS[d][i];source={'domain':'numbers','examples':[[1,2+i],[2,4+i]]};target={'domain':'quantities' if d==6 else 'numbers','values':[101+i,201+i],'structure':'paired-counts' if d in(4,6) else 'scalar-prediction'}
  out.append({'id':base['id'].replace('ADAPT','LEARN'),'domain':'LEARN-%03d'%d,'seed':base['seed'],'difficulty':base['difficulty'],'track':'infrastructure' if d in(1,5) else 'native','input':{'kind':k,'key':'experience-'+str(j),'initial_input':i+1,'experience':{'reported_outcome':'FAILED' if d==5 else 'REPORTED','feedback':'check-input','error':'HOST_REPORTED_ERROR' if d==5 else 'NONE'},'source':source,'subsequent_input':target,'control':{'experience':None,'target':target.copy(),'criterion':'exact-output'},'criterion':'exact-output','isolation':'separate-instances'}})
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','seed','difficulty','track','input'},'CASE');ident(t['id']);need(t['domain']in ['LEARN-%03d'%i for i in range(1,7)],'DOMAIN');d=int(t['domain'][-3:]);need(t['track']==('infrastructure' if d in(1,5) else 'native'),'TRACK');need(type(t['seed'])is int and t['seed']in(1001,2003),'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');x=t['input'];need(type(x)is dict and set(x)=={'kind','key','initial_input','experience','source','subsequent_input','control','criterion','isolation'},'INPUT');need(x['kind']in KINDS[d],'KIND');ident(x['key']);need(type(x['initial_input'])is int and 1<=x['initial_input']<=8,'INITIAL');need(x['experience']=={'reported_outcome':'FAILED' if d==5 else 'REPORTED','feedback':'check-input','error':'HOST_REPORTED_ERROR' if d==5 else 'NONE'},'EXPERIENCE');s=x['source'];target=x['subsequent_input'];need(type(s)is dict and set(s)=={'domain','examples'} and s['domain']=='numbers' and type(s['examples'])is list and len(s['examples'])==2,'SOURCE')
 for e in s['examples']:need(type(e)is list and len(e)==2 and all(type(v)is int and 0<=v<=100 for v in e),'EXAMPLE')
 need(type(target)is dict and set(target)=={'domain','values','structure'} and target['domain']in('numbers','quantities') and target['structure']in('paired-counts','scalar-prediction') and type(target['values'])is list and len(target['values'])==2 and all(type(v)is int and 100<=v<=300 for v in target['values']),'TARGET');need(not set(e[0] for e in s['examples'])&set(target['values']),'HOLDOUT');need(x['control']=={'experience':None,'target':target,'criterion':'exact-output'} and x['criterion']=='exact-output' and x['isolation']=='separate-instances','CONTROL');canonical(t);return t
def reference(t):
 validate(t);x=t['input'];k=x['kind']
 if t['track']=='native':return None
 codes={'missing':'MISSING','invalid_id':'INVALID_IDENTITY','bad_provenance':'INVALID_DIGEST','duplicate_evidence':'EVIDENCE_DUPLICATE','conflicting':'CONFLICTING_RETRY'}
 if k in codes:return {'rejection':codes[k],'memory_unchanged':True,'retained':x['experience'],'verification_status':'UNVERIFIED'}
 if k=='retry':return {'retained':x['experience'],'verification_status':'UNVERIFIED','state':'SUCCEEDED','attempt':2,'stale_rejection':'LEASE_STATE','action_origin':'HOST_SELECTED','learning':False}
 return {'retained':x['experience'],'verification_status':'UNVERIFIED','control':'MISSING','learning':False}
