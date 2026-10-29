import unittest,json,copy,pathlib,hashlib,ast
from dataclasses import asdict
from test_cognitive_model_planning import setup
from cognitive_provider_contracts import *
from cognitive_provider_adapter import invoke_provider

def corrupt(x,**kw):
    y=copy.copy(x)
    for k,v in kw.items(): object.__setattr__(y,k,v)
    return y

def fixture():
    s,p,o=setup(); policy=ProviderPolicyV1((('local','model'),),8192,8192,100,1000)
    args=dict(request_id='00000000-0000-0000-0000-000000000009',planning_request=p,provider_id='local',model_id='model',max_input_bytes=8192,max_output_bytes=8192,max_output_tokens=100,max_latency_ms=1000,max_attempts=1)
    r=ProviderRequestV1(**args,request_commitment=commitment('COGProviderRequestV1',args))
    return s,r,policy,response(r,json.dumps(o).encode())

def response(r,raw):
    args=dict(request_id=r.request_id,provider_id=r.provider_id,model_id=r.model_id,raw_output=raw,reported_output_tokens=10,reported_latency_ms=2,finish_reason='STOP')
    return ProviderResponseV1(**args,response_commitment=commitment('COGProviderResponseV1',args))

def resign(obj,field): return corrupt(obj,**{field:commitment('COGProviderRequestV1' if field=='request_commitment' else 'COGProviderResponseV1',body(obj,field))})

class Tests(unittest.TestCase):
    def call(self,rchange=None,qchange=None,policy=None,exc=False,rehash=False):
        s,r,p,q=fixture(); calls=[]
        if rchange: r=corrupt(r,**rchange)
        if qchange: q=corrupt(q,**qchange)
        if rehash:
            r=resign(r,'request_commitment'); q=resign(q,'response_commitment')
        def transport(x):
            calls.append((x.provider_id,x.model_id))
            if exc: raise RuntimeError('sensitive message')
            return q
        before=asdict(s); d=invoke_provider(s,r,policy or p,transport)
        self.assertEqual(asdict(s),before); self.assertEqual(d.attempts_used,len(calls)); self.assertFalse(d.executable); self.assertFalse(d.production_authorized); self.assertFalse(d.trusted_verification)
        return d,calls
    def reject(self,expected,**kw):
        d,c=self.call(**kw); self.assertEqual(d.reason_code,expected); self.assertIsNone(d.validated_plan); return c
    def test_positive(self): self.assertIsNotNone(self.call()[0].validated_plan)
    def test_cog008(self):
        s,r,p,q=fixture(); q=response(r,b'{}'); d=invoke_provider(s,r,p,lambda _:q); self.assertEqual(d.reason_code,'COG008_FIELDS')
    def test_provider(self): self.assertEqual(self.reject('PROVIDER_MODEL_NOT_ALLOWED',rchange={'provider_id':'other'},rehash=True),[])
    def test_model(self): self.assertEqual(self.reject('PROVIDER_MODEL_NOT_ALLOWED',rchange={'model_id':'other'},rehash=True),[])
    def test_request_commitment(self): self.assertEqual(self.reject('REQUEST_COMMITMENT',rchange={'request_commitment':'0'*64}),[])
    def test_input_size(self): self.assertEqual(self.reject('INPUT_SIZE',rchange={'max_input_bytes':1},rehash=True),[])
    def test_output_size(self): self.reject('OUTPUT_SIZE',rchange={'max_output_bytes':1},rehash=True)
    def test_request_id(self): self.reject('RESPONSE_BINDING',qchange={'request_id':'00000000-0000-0000-0000-000000000088'},rehash=True)
    def test_provider_substitution(self): self.reject('RESPONSE_BINDING',qchange={'provider_id':'other'},rehash=True)
    def test_model_substitution(self): self.reject('RESPONSE_BINDING',qchange={'model_id':'other'},rehash=True)
    def test_response_commitment(self): self.reject('RESPONSE_COMMITMENT',qchange={'response_commitment':'0'*64})
    def test_negative_tokens(self): self.reject('NUMBER',qchange={'reported_output_tokens':-1})
    def test_latency_type(self):
        for value in (-1,True,float('nan'),1.5): self.reject('NUMBER',qchange={'reported_latency_ms':value})
    def test_token_limit(self): self.reject('TOKEN_LIMIT',qchange={'reported_output_tokens':101},rehash=True)
    def test_latency_limit(self): self.reject('LATENCY_LIMIT',qchange={'reported_latency_ms':1001},rehash=True)
    def test_finish(self): self.reject('FINISH_REASON',qchange={'finish_reason':'TOOL_CALL'})
    def test_truncated(self): self.reject('FINISH_REASON',qchange={'finish_reason':'LENGTH'})
    def test_exception(self): self.assertEqual(len(self.reject('TRANSPORT_EXCEPTION',exc=True)),1)
    def test_determinism(self): self.assertEqual(self.call()[0],self.call()[0])
    def test_attempts(self): self.assertEqual(self.call()[0].attempts_used,1)
    def test_no_retry(self): self.assertEqual(self.reject('V1_LIMIT',rchange={'max_attempts':2},rehash=True),[])
    def test_no_fallback(self): self.assertEqual(self.reject('FINISH_REASON',qchange={'finish_reason':'LENGTH'}),[('local','model')])
    def test_unexpected(self):
        s,r,p,q=fixture(); self.assertEqual(invoke_provider(s,r,p,lambda _:{}).reason_code,'RESPONSE_TYPE')
    def test_scope_preflight(self):
        s,r,p,q=fixture(); calls=[]; s=corrupt(s,task=corrupt(s.task,objective='other')); d=invoke_provider(s,r,p,lambda _:calls.append(1)); self.assertEqual(calls,[])
    def test_no_effects(self):
        tree=ast.parse(pathlib.Path(__file__).with_name('cognitive_provider_adapter.py').read_text())
        modules={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(modules,{'dataclasses','cognitive_contracts','cognitive_model_planning_contracts','cognitive_model_planning','cognitive_provider_contracts'})
    def test_integrity(self):
        root=pathlib.Path(__file__).resolve().parent.parent; inv=root/'cog009a-integrity.json'
        if not inv.exists(): self.skipTest('external original inventory required')
        for f,h in json.loads(inv.read_text()).items(): self.assertEqual(hashlib.sha256((root/f).read_bytes()).hexdigest(),h)

if __name__=='__main__': unittest.main()
