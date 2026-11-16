from skynet_adaptation_validation.benchmark import generate as grid
from skynet_validation.evidence import need,ident,canonical
KINDS={1:('valid','unauthorized','duplicate','missing','invalid_id','unauthorized','duplicate','missing'),2:('complete','pending','stale_attempt','unavailable')*2,3:('success','failure')*4,4:('priority','capacity','unavailable','combined_dependency')*2,5:('worker_failure','requeue','release','exhausted','worker_failure','requeue','lease_expired','invalid_retry'),6:('goal',)*8}
def generate():
 out=[]
 for j,b in enumerate(grid()):
  d=j//8+1;i=j%8;out.append({'id':b['id'].replace('ADAPT','AUTO'),'domain':'AUTO-%03d'%d,'seed':b['seed'],'difficulty':b['difficulty'],'track':'native' if d==6 else 'infrastructure','input':{'kind':KINDS[d][i],'count':2+i%3,'priority':i+1,'value':100*d+i,'goal':'complete-supplied-work' if d!=6 else 'derive-plan-and-achieve-goal','plan_origin':'HOST' if d!=6 else 'NATIVE_REQUIRED'}})
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','seed','difficulty','track','input'},'CASE');ident(t['id']);need(t['domain']in ['AUTO-%03d'%i for i in range(1,7)],'DOMAIN');d=int(t['domain'][-3:]);need(t['track']==('native' if d==6 else 'infrastructure'),'TRACK');need(type(t['seed'])is int and t['seed']in(1001,2003),'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');x=t['input'];need(type(x)is dict and set(x)=={'kind','count','priority','value','goal','plan_origin'},'INPUT');need(x['kind']in KINDS[d],'KIND');need(type(x['count'])is int and 2<=x['count']<=4 and type(x['priority'])is int and 1<=x['priority']<=8 and type(x['value'])is int and 100<=x['value']<=607,'NUMBER');need(x['goal']==('complete-supplied-work' if d!=6 else 'derive-plan-and-achieve-goal') and x['plan_origin']==('HOST' if d!=6 else 'NATIVE_REQUIRED'),'CONTROL');canonical(t);return t
def mapped(t):
 x=t['input'];d=t['domain']
 if d=='AUTO-003':return {'id':t['id'],'domain':'PLAN-005','track':'infrastructure','seed':t['seed'],'difficulty':t['difficulty'],'input':{'goal_id':'supplied-goal','count':x['count'],'kind':x['kind'],'priorities':[0]*x['count'],'value':x['value']}}
 return {'id':t['id'],'domain':'ADAPT-005' if x['kind']=='combined_dependency' else ('ADAPT-001' if x['kind']=='unavailable' else ('ADAPT-003' if d=='AUTO-004' else 'ADAPT-002')),'track':'infrastructure','seed':t['seed'],'difficulty':t['difficulty'],'input':{'kind':x['kind'],'priority':x['priority'],'marker':x['value'],'baseline':'available workers; eligible task; original host strategy','changed':x['kind']}}
