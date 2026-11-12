from skynet_validation.evidence import need,ident,canonical
KINDS={1:('unavailable','reactivate','invalid_status','unavailable','reactivate','invalid_status','unavailable','reactivate'),2:('worker_failure','requeue','release','exhausted')*2,3:('capacity','priority','missing','cycle')*2,4:('selection',)*8,5:('combined_missing','combined_cycle','combined_priority','combined_dependency')*2,6:('revision',)*8}
def generate():
 out=[]
 for d in range(1,7):
  for i,k in enumerate(KINDS[d]):
   out.append({'id':'ADAPT-%03d-%04d'%(d,i+1),'domain':'ADAPT-%03d'%d,'seed':(1001,2003)[i%2],'difficulty':('basic','intermediate','advanced')[i%3],'track':'native' if d in(4,6) else 'infrastructure','input':{'kind':k,'priority':i+1,'marker':d*100+i,'baseline':'available workers; eligible task; original host strategy','changed':k}})
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','seed','difficulty','track','input'},'CASE');ident(t['id']);need(t['domain']in ['ADAPT-%03d'%i for i in range(1,7)],'DOMAIN');d=int(t['domain'][-3:]);need(t['track']==('native' if d in(4,6) else 'infrastructure'),'TRACK');need(type(t['seed'])is int and t['seed']in(1001,2003),'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');x=t['input'];need(type(x)is dict and set(x)=={'kind','priority','marker','baseline','changed'},'INPUT');need(x['kind']in KINDS[d] and x['changed']==x['kind'],'KIND');need(type(x['priority'])is int and 1<=x['priority']<=8 and type(x['marker'])is int and 100<=x['marker']<=607,'NUMBER');need(x['baseline']=='available workers; eligible task; original host strategy','BASELINE');canonical(t);return t
def reference(t):
 validate(t);k=t['input']['kind']
 if t['track']=='native':return None
 if k in ('worker_failure','requeue'):return {'baseline':'SUCCEEDED','state':'SUCCEEDED','attempt':2,'stale_code':'LEASE_STATE'}
 if k=='release':return {'baseline':'SUCCEEDED','state':'CANCELLED','attempt':1,'stale_code':'LEASE_STATE'}
 if k=='exhausted':return {'baseline':'SUCCEEDED','state':'FAILED','attempt':1,'stale_code':'LEASE_STATE','retry_accepted':False,'retry_reason':'ValueError:REJECTED:RETRY_STATE'}
 if k=='invalid_status':return {'code':'WORKER_STATE','unchanged':True,'baseline_running':2}
 if k in ('missing','combined_missing'):return {'code':'UNKNOWN_DEPENDENCY','unchanged':True,'baseline_running':2}
 if k in ('cycle','combined_cycle'):return {'code':'CYCLE','unchanged':True,'baseline_running':2}
 if k=='unavailable':return {'running':0,'ready':2,'selected':[],'baseline_running':2}
 if k=='combined_dependency':return {'running':1,'ready':0,'selected':['g0'],'baseline_running':2,'waiting':1}
 if k in ('capacity','priority','combined_priority'):return {'running':1,'ready':1,'selected':['g1' if k!='capacity' else 'g0'],'baseline_running':2}
 return {'running':2,'ready':0,'selected':['g0','g1'],'baseline_running':2}
