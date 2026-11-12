import inspect,hashlib
from dataclasses import replace
from .cases import mapped
from skynet_autonomy_validation.adapter import execute as auto
from skynet_adaptation_validation.adapter import execute as adapt
from skynet_memory_validation.adapter import execute as memory
from skynet_metacognition_validation.adapter import execute as meta
from skynet_validation.evidence import commitment
from skynet_validation.registry import registry
from skynet.system import System,T
from skynet_sys.tasks import TaskRequest
from skynet_sys.canonical import FrozenJSON
from skynet_sys.messages import Message
from skynet_sys_transport.bus import Bus
from skynet_sys_transport.contracts import Config
from skynet_sys_verification import Engine
OWN={'schema','missing_field','wrong_type','unsupported','arity','concurrency','queue'}
def discover():
 objects={'System._apply':System._apply,'Engine.evaluate':Engine.evaluate,'registry':registry};b={'classification':'UNAVAILABLE','scope':'Exported reference-system interfaces; not universal proof of absence','sources':{k:hashlib.sha256(inspect.getsource(v).encode()).hexdigest() for k,v in objects.items()},'reason':'Host-selected operations and fixed voting/constraint rules; no exported uncertainty-sensitive reasoning/selection interface.'};return dict(b,commitment=commitment('val009-admission',b))
def execute(t):
 if t['track']=='native':raise ValueError('NATIVE_INTERFACE_UNAVAILABLE')
 k=t['input']['kind']
 if k not in OWN:
  m=mapped(t);o={'AUTO':auto,'ADAPT':adapt,'MEM':memory,'META':meta}[m['domain'].split('-')[0]](m);return {'status':o['status'],'answer':o['answer'],'calls':o['calls'],'details':{'initial_and_final_observations':o['details'],'actual_fixture':m,'injection':k,'recovery_selection':'HOST_EXPLICIT_RULE','scope':'Isolated local fixture; deterministic response, no native uncertainty inference'},'classification':'INFRASTRUCTURE_AUTOMATION'}
 h=System(1,1);calls=[];code='ACCEPTED';before=h.state_digest();initial={'digest':before,'tasks':h.rows()}
 try:
  if k in('schema','missing_field','wrong_type'):
   kw=dict(task_id='task',parent_task_id=None,trace_id='trace',requester_id='admin',capability_required='cognitive.reason',payload=FrozenJSON.make({}),priority=0,deadline='2026-10-25T00:01:00.000000Z',idempotency_key='key',created_at=T)
   if k=='schema':kw['schema_version']='unsupported'
   elif k=='missing_field':del kw['task_id']
   else:kw['priority']='bad'
   calls.append('TaskRequest.constructor');TaskRequest(**kw)
  elif k=='queue':
   b=Bus(replace(h.bus.config,queue_limit=1),h.bus.topics,replace(h.bus.authority,rights=h.bus.authority.rights+(('consumer','poll','system.audit'),)));b.subscribe('consumer','system.audit','audit',0)
   def msg(n):return Message('m'+str(n),'trace',None,None,'admin',b.config.bus_id,'EVIDENCE_ATTACHED',FrozenJSON.make({'n':n}),T,b.config.at(1))
   b.publish('admin','system.audit',msg(0),0);initial={'inspection':str(b.inspect('admin',0))};before=b.inspect('admin',0).published_total if hasattr(b.inspect('admin',0),'published_total') else None
   calls.extend(['Bus.subscribe','Bus.publish(initial)','Bus.publish(over capacity)']);b.publish('admin','system.audit',msg(1),0)
  else:
   calls.append('System.run');h.run('unknown' if k=='unsupported' else 'dispatch',*(() if k in('unsupported','arity') else (0,)))
 except (ValueError,TypeError) as e:code='TypeError' if type(e)is TypeError else str(e)
 if k=='queue':
  inspection=b.inspect('admin',0);final={'inspection':str(inspection)};unchanged= b.poll('consumer','audit',0).message_id=='m0' and b.poll('consumer','audit',0)is None;calls+=['Bus.inspect','Bus.poll(original)','Bus.poll(no additional delivery)']
 else:final={'digest':h.state_digest(),'tasks':h.rows()};unchanged=h.state_digest()==initial['digest']
 return {'status':'EXECUTED','answer':{'code':code,'protected_state_unchanged':unchanged},'calls':calls,'details':{'initial':initial,'fault':k,'final':final,'boundary':'Component state; rejection audit may grow','invariant':'No malformed admission or excess delivery'},'classification':'INFRASTRUCTURE_AUTOMATION'}
