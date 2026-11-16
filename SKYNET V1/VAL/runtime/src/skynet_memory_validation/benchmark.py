"""Evaluator-owned definitions; never imported by the native adapter."""
from skynet_validation.evidence import need,ident,canonical
KINDS={1:('create','duplicate','invalid_id','conflicting_duplicate','create','duplicate','invalid_id','conflicting_duplicate'),2:('lookup','many','missing','invalid_lookup','lookup','many','missing','invalid_lookup'),3:('update','cas','restore','snapshot','update','cas','restore','snapshot'),4:('context',)*8,5:('transfer',)*8,6:('bad_provenance','duplicate_evidence','stale','tamper','unverified','bad_provenance','tamper','unverified')}
def generate():
 out=[]
 for d in range(1,7):
  for i,k in enumerate(KINDS[d]):
   x={'key':'record-'+str(i),'value':1000*d+i,'kind':k}
   if d in (4,5):x.update(source={'task':'store-factor','factor':i+2},target={'task':'apply-to-new-batch' if d==5 else 'use-stored-factor','items':[i+1,i+3]},control={'prior_information':False,'target':'identical'},isolation='fresh-condition-instances')
   out.append({'id':'MEM-%03d-%04d'%(d,i+1),'domain':'MEM-%03d'%d,'seed':(1001,2003)[i%2],'difficulty':('basic','intermediate','advanced')[i%3],'track':'native' if d in (4,5) else 'infrastructure','input':x})
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','seed','difficulty','track','input'},'CASE');ident(t['id']);need(t['domain']in ['MEM-%03d'%i for i in range(1,7)],'DOMAIN');d=int(t['domain'][-3:]);need(t['track']==('native' if d in(4,5) else 'infrastructure'),'TRACK');need(type(t['seed'])is int and t['seed']in(1001,2003),'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');x=t['input'];need(type(x)is dict and x.get('kind')in KINDS[d],'KIND');need(set(x)==({'key','value','kind','source','target','control','isolation'} if d in(4,5) else {'key','value','kind'}),'INPUT_FIELDS');ident(x['key']);need(type(x['value'])is int and 0<=x['value']<=1000000,'VALUE');
 if d in(4,5):
  need(type(x['source'])is dict and set(x['source'])=={'task','factor'} and x['source']['task']=='store-factor' and type(x['source']['factor'])is int and 2<=x['source']['factor']<=9,'SOURCE');need(type(x['target'])is dict and set(x['target'])=={'task','items'} and x['target']['task']==('apply-to-new-batch' if d==5 else 'use-stored-factor') and type(x['target']['items'])is list and len(x['target']['items'])==2 and all(type(v)is int and 1<=v<=10 for v in x['target']['items']),'TARGET');need(x['control']=={'prior_information':False,'target':'identical'} and x['isolation']=='fresh-condition-instances','CONTROL')
 canonical(t);return t
def reference(t):
 validate(t);x=t['input'];k=x['kind']
 if t['track']=='native':return None
 codes={'invalid_id':'INVALID_IDENTITY','conflicting_duplicate':'CONFLICTING_RETRY','missing':'MISSING','invalid_lookup':'MISSING','cas':'VERSION_CONFLICT','stale':'VERSION_CONFLICT','bad_provenance':'INVALID_DIGEST','duplicate_evidence':'EVIDENCE_DUPLICATE','tamper':'SNAPSHOT_TAMPERED'}
 if k in codes:return {'code':codes[k],'record_state_unchanged':True}
 if k=='restore':return {'value':x['value'],'version':3,'status':'RESTORED','history_length':3}
 if k=='snapshot':return {'snapshot_valid':True,'unchanged':True}
 return {'value':x['value']+int(k=='update'),'version':2 if k=='update' else 1,'evidence_status':'UNVERIFIED'}
