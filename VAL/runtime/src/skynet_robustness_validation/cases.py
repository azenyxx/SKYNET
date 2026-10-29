from skynet_validation.evidence import need,canonical
from skynet_autonomy_validation.cases import generate as auto
from skynet_adaptation_validation.benchmark import generate as adapt
from skynet_memory_validation.benchmark import generate as memory
from skynet_metacognition_validation.benchmark import generate as meta
KINDS={1:('schema','missing_field','wrong_type','invalid_id','unauthorized','duplicate','unsupported','arity'),2:('missing','cycle','unavailable','pending','insufficient','opposite','missing','cycle'),3:('worker_failure','requeue','release','exhausted','lease_expired','invalid_retry','pending','failure'),4:('tamper','bad_provenance','duplicate_evidence','stale','conflicting_duplicate','invalid_state','corrupt_evidence','bad_again'),5:('capacity','priority','unavailable','queue','concurrency','duplicate','capacity','queue'),6:('uncertainty',)*8}
def generate():
 return [{'id':'ROBUST-%03d-%04d'%(d,i+1),'domain':'ROBUST-%03d'%d,'track':'native' if d==6 else 'infrastructure','seed':(1001,2003)[i%2],'difficulty':('basic','intermediate','advanced')[i%3],'input':{'kind':k,'variant':i,'origin':'HOST_FAULT_INJECTION' if d!=6 else 'NATIVE_REQUIRED'}} for d in range(1,7) for i,k in enumerate(KINDS[d])]
def validate(t):
 need(type(t)is dict and set(t)=={'id','domain','track','seed','difficulty','input'},'CASE');need(t in generate(),'CASE_BINDING');canonical(t);return t
def mapped(t):
 d=int(t['domain'][-3:]);k=t['input']['kind'];i=t['input']['variant']
 if d==1 and k in('invalid_id','unauthorized','duplicate') or d==5 and k=='duplicate':pool=auto();dom='AUTO-001'
 elif d==2 and k=='pending' or d==3 and k=='pending':pool=auto();dom='AUTO-002'
 elif d==3 and k=='failure':pool=auto();dom='AUTO-003'
 elif d==3:pool=auto();dom='AUTO-005'
 elif d==4 and k in('invalid_state','corrupt_evidence','bad_again') or d==2 and k in('insufficient','opposite'):pool=meta();dom='META-006' if k in('bad_again','insufficient','opposite') else 'META-002'
 elif d==4:pool=memory();dom='MEM-001' if k=='conflicting_duplicate' else 'MEM-006'
 elif k=='unavailable':pool=adapt();dom='ADAPT-001'
 else:pool=adapt();dom='ADAPT-003'
 rows=[v for v in pool if v['domain']==dom and v['input']['kind']==k];return rows[i%len(rows)]
