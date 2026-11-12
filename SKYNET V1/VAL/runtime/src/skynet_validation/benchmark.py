"""Oracles live in the evaluator process and are never imported by adapter."""
from .evidence import VERSION,commitment,need,validate_task
GENERATOR_VERSION='val001-generator-v2'
SEEDS=(1001,2003)
PARTITIONS=('development','validation','holdout')
def reference(task):
 d=task['domain'];x=task['input']
 if d in ('CAP-001','CAP-008'):
  votes=x['votes'];required=3 if x['policy']=='all' else (2 if x['policy']=='quorum' else 1)
  verdict='INCONCLUSIVE' if len(votes)<required or len(set(votes))!=1 else votes[0]
  return {'verdict':verdict,'conflict':('PASS'in votes and 'FAIL'in votes),'evidence_status':['UNVERIFIED']*len(votes)}
 if d=='CAP-002':return {'scheduler':'SUCCEEDED','worker':'COMPLETED','decision':'PASS','binding':True}
 if d=='CAP-004':return {'states':['FAILED']*x['count'] if x['fail_first'] else ['SUCCEEDED']*x['count'],'initial':['READY']+['WAITING']*(x['count']-1)}
 if d=='CAP-005':return {'value':x['value'],'version':1,'stale_code':'VERSION_CONFLICT','unchanged':True,'provenance_status':'UNVERIFIED'}
 if d=='CAP-007':return {'scheduler':'RUNNING' if x['action']=='RETRY' else 'CANCELLED','old_lease':'REVOKED','new_attempt':2 if x['action']=='RETRY' else 1,'stale_code':'LEASE_STATE'}
 return None

def generate(partition,freeze_commitment=None):
 need(partition in PARTITIONS,'PARTITION')
 if partition=='holdout':
  from .evidence import hashcheck
  hashcheck(freeze_commitment)
 out=[]
 for domain in range(1,11):
  for i in range(4):
   seed=((int(freeze_commitment[(i%2)*8:(i%2+1)*8],16)%900000)+10000) if partition=='holdout' else SEEDS[i%2];idx=PARTITIONS.index(partition)*4+i;level=('basic','intermediate','advanced')[idx%3];n=idx%3+1;value=seed+idx*17
   # Input variation is independent of system outputs. Distinct families stay unsupported.
   d='CAP-%03d'%domain
   if domain in (1,8):
    policy=('single','quorum','all')[idx%3];votes=(['PASS'],['PASS','FAIL'],[],['PASS','PASS'],['FAIL','FAIL','FAIL'],['PASS','PASS','PASS'])[idx%6]
    if policy=='single':votes=votes[:1]
    x={'policy':policy,'votes':votes,'label':'case-'+str(value)}
   elif domain==2:x={'count':n+PARTITIONS.index(partition)*3,'task':'t'+str(idx%(n+PARTITIONS.index(partition)*3))}
   elif domain==4:x={'count':n+PARTITIONS.index(partition)*3,'fail_first':idx%2==1,'label':'graph-'+str(value)}
   elif domain==5:x={'value':value,'record_id':'record-'+str(value)}
   elif domain==7:x={'action':'RETRY' if idx%2==0 else 'RELEASE_LEASE','operation_id':'recover-'+str(value)}
   else:x={'problem':{3:'Decompose a novel goal',6:'Transfer learned rule to unseen structure',9:'Find and repair an erroneous intermediate inference',10:'Solve an unseen reasoning family'}[domain],'instance':value,'depth':n}
   task=dict(schema=VERSION,case_id=d+'-'+partition+'-'+str(i),domain=d,seed=seed,difficulty=level,partition=partition,input=x);validate_task(task)
   out.append((task,reference(task)))
 return out
