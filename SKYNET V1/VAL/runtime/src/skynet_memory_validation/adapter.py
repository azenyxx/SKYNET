"""Actual Store API observations only. No reference evaluator or transfer solver."""
from dataclasses import replace
from skynet_sys_memory.store import Store,Namespace,Operation,MemoryError
from skynet_sys.capabilities import HostPolicy
from skynet_sys.canonical import FrozenJSON,digest
from skynet_sys.evidence import EvidenceReference
from skynet_sys.errors import ContractError
from skynet_validation.registry import registry
from skynet_validation.evidence import commitment
T='2026-10-25T00:00:00.000000Z'
def execute(t):
 x=t['input'];k=x['kind'];calls=[];details={}
 if t['track']=='native':
  rows=registry();row=next(v for v in rows if v['capability_id']==('CAP-006' if k=='transfer' else 'CAP-005'))
  assert (row['execution_interface'] is None if k=='transfer' else row['measurement_kind']=='STORAGE')
  return {'status':'UNAVAILABLE','answer':None,'calls':[],'details':{'registry':row,'conditions_executed':False,'reason':'No exported native contextual-use/transfer interface; source/target/control not executed.'},'interface':'skynet_validation.registry.registry'}
 s=Store(HostPolicy('policy',(('host','memory.read'),('host','memory.write'))),(Namespace('agent:memory','host',('host',),('host',),versions=16),))
 key=x['key'];payload=FrozenJSON.make({'value':x['value']});ev=EvidenceReference('evidence','host',key,digest('payload',payload),'diagnostic',T,'UNVERIFIED')
 def write(tx,key=key,value=payload,version=0,kind='CREATE',evidence=(ev,),tick=1):
  calls.append('skynet_sys_memory.store.Store.transact');return s.transact('host',tx,(Operation('agent:memory',key,kind,version,value,evidence),),tick)
 def read(key=key):calls.append('skynet_sys_memory.store.Store.read');return s.read('host','agent:memory',key)
 # Every rejection starts from a real committed record, including malformed follow-up writes.
 write('initial');before=s.digest();details['pre_state_digest']=before
 try:
  if k=='duplicate':write('initial')
  elif k=='invalid_id':write('invalid',key='bad key')
  elif k=='conflicting_duplicate':write('initial',value=FrozenJSON.make({'value':-1}))
  elif k=='many':
   for j in range(3):write('extra'+str(j),key='extra'+str(j),tick=j+2)
  elif k=='missing':read('absent')
  elif k=='invalid_lookup':read('invalid key')
  elif k=='update':write('update',value=FrozenJSON.make({'value':x['value']+1}),version=1,kind='UPDATE',tick=2)
  elif k in ('cas','stale'):write('stale',version=0,kind='UPDATE',tick=2)
  elif k=='restore':
   calls.append('skynet_sys_memory.store.Store.snapshot');snap=s.snapshot('host','checkpoint');write('changed',value=FrozenJSON.make({'value':-1}),version=1,kind='UPDATE',tick=2)
   calls.append('skynet_sys_memory.store.Store.restore_checkpoint');result=s.restore_checkpoint('host',s.component_id,'checkpoint',s.digest(),'DIAGNOSTIC_FORWARD_V1','restore');r=read();details['restore_audit']=result.audit_commitment
   answer={'value':r.payload.value()['value'],'version':r.version,'status':result.restoration_status,'history_length':len(s.history('host','agent:memory',key))}
  elif k in ('snapshot','tamper'):
   calls.append('skynet_sys_memory.store.Store.snapshot');snap=s.snapshot('host','snapshot')
   calls.append('skynet_sys_memory.store.Store.verify_snapshot');s.verify_snapshot(replace(snap,commitment='0'*64) if k=='tamper' else snap);answer={'snapshot_valid':True,'unchanged':s.digest()==before}
  elif k=='bad_provenance':
   calls.append('skynet_sys.evidence.EvidenceReference');bad=EvidenceReference('bad','host',key,'synthetic','diagnostic',T,'UNVERIFIED');write('bad',evidence=(bad,))
  elif k=='duplicate_evidence':write('badrefs',key='another',evidence=(ev,ev))
  if k not in ('restore','snapshot'):
   r=read();answer={'value':r.payload.value()['value'],'version':r.version,'evidence_status':r.evidence_refs[0].verification_status}
 except (MemoryError,ContractError) as e:
  answer={'code':str(e),'record_state_unchanged':s.digest()==before};details['exception_type']=type(e).__name__
 details['post_state_digest']=s.digest();details['record_commitment']=read().commitment;details['evidence_commitment']=ev.commitment;details['calls']=calls[:]
 return {'status':'EXECUTED','answer':answer,'calls':calls,'details':details,'interface':'skynet_sys_memory.store.Store'}
