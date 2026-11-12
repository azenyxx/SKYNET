from .contracts import *
def generate():
 out=[]
 for d in range(1,7):
  for i in range(8):
   seed=(1001,2003)[i%2];n=2+i%3;kind={1:'represent',2:'decompose',3:('cycle' if i%2==0 else 'missing') if i<6 else 'valid',4:'unavailable' if i in(2,5) else 'capacity',5:'failure' if i<3 else 'success',6:('worker_failure' if i<3 else ('requeue' if i<6 else 'release'))}[d]
   t={'id':'PLAN-%03d-%d'%(d,i),'domain':'PLAN-%03d'%d,'track':'native_planning' if d==2 else 'infrastructure','seed':seed,'difficulty':('basic','intermediate','advanced')[i%3],'input':{'goal_id':'goal:'+str(seed)+':'+str(i),'count':n,'kind':kind,'priorities':[(i+j*3)%10 for j in range(n)],'value':seed+i}};validate(t);out.append(t)
 return out

def dependencies(x):
 n=x['count'];rows={str(i):([str(i-1)] if i else []) for i in range(n)}
 if x['kind']=='cycle':rows['0']=[str(n-1)]
 if x['kind']=='missing':rows['0']=['absent']
 return rows

def graph_reference(rows):
 if any(d not in rows for deps in rows.values() for d in deps):return 'UNKNOWN_DEPENDENCY'
 pending=set(rows);done=set()
 while pending:
  ready={k for k in pending if set(rows[k])<=done}
  if not ready:return 'CYCLE'
  done|=ready;pending-=ready
 return 'OK'

def reference(t):
 validate(t);x=t['input'];d=t['domain'];n=x['count']
 if d=='PLAN-002':return None
 if d=='PLAN-001':return {'goal_id':x['goal_id'],'preconditions':['authorized'],'required_outcome':x['value'],'dependencies':['external'],'completion_criteria':'reported_success'}
 if d=='PLAN-003':
  code=graph_reference(dependencies(x));return {'code':code,'accepted':code=='OK','unchanged_on_rejection':True if code!='OK' else None}
 if d=='PLAN-004':
  winner=max(range(n),key=lambda i:(x['priorities'][i],-i)) if x['kind']!='unavailable' else None
  return {'states':['RUNNING' if i==winner else 'READY' for i in range(n)],'running':0 if winner is None else 1}
 if d=='PLAN-005':return {'states':['FAILED']*n if x['kind']=='failure' else ['SUCCEEDED']*n,'completed':0 if x['kind']=='failure' else n,'dependency_preserved':True,'failure_propagated':x['kind']=='failure'}
 return {'scheduler':'CANCELLED' if x['kind']=='release' else 'SUCCEEDED','attempt':1 if x['kind']=='release' else 2,'old_lease':'REVOKED','stale_code':'LEASE_STATE'}
