import unittest,json,pathlib,hashlib,copy
from dataclasses import replace,asdict
from decimal import Decimal as D
from unittest.mock import patch
from test_cognitive_provider_adapter import fixture as prior,resign
from cognitive_live_provider import *
from cognitive_live_provider_security import IsolatedBudgetLedger

def fixture():
    s,r,p,q=prior(); r=resign(replace_unchecked(r,provider_id='openai'),'request_commitment'); p=replace(p,allowed_provider_models=(('openai','model'),))
    c=LiveProviderConfigV1('openai','model',ENDPOINT,100,100,500,8192,16384,100,1,D('1'),('api.openai.com',),'synthetic-v1')
    price=PricePolicyV1('synthetic-v1',('model',),D('0.000001'),D('0.000002'),10000)
    envelope={'status':'completed','model':'model','output':[{'type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':q.raw_output.decode()}]}],'usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30}}
    return s,r,p,c,price,envelope

def replace_unchecked(x,**kw):
    x=copy.copy(x)
    for k,v in kw.items(): object.__setattr__(x,k,v)
    return x

class Tests(unittest.TestCase):
    def run_case(self,config=None,change=None,status=200,error=None,key=True,clock=None):
        s,r,p,c,price,e=fixture(); c=replace(c,network_enabled=True,**(config or {}))
        if change: change(e)
        calls=[]; lookups=[]; ledger=IsolatedBudgetLedger(D('2'),isolated_single_process=True); before=asdict(s)
        def secret(): lookups.append(1); return 'synthetic' if key else None
        def http(cfg,body,credential,deadline,timer):
            calls.append(1); b=json.loads(body); self.assertFalse(b['store']); self.assertFalse(b['stream']); self.assertEqual(b['tools'],[])
            if error: raise LiveError(error)
            return status,json.dumps(e).encode()
        with patch('http.client.HTTPSConnection',side_effect=AssertionError('real network forbidden')):
            result=invoke_live(s,r,p,c,price,secret,ledger,http_transport=http,clock=clock or (lambda:0.0))
        self.assertEqual(asdict(s),before); self.assertFalse(result.executable); self.assertFalse(result.production_authorized)
        self.assertEqual(result.http_attempts,len(calls)); return result,calls,lookups,ledger,r
    def test_default_disabled(self):
        s,r,p,c,price,e=fixture(); d=invoke_live(s,r,p,c,price,lambda:self.fail(),None,http_transport=lambda *a:self.fail()); self.assertEqual(d.reason_code,'NETWORK_DISABLED')
    def test_positive(self): self.assertIsNotNone(self.run_case()[0].downstream.validated_plan)
    def test_missing_secret(self):
        d,c,_,l,r=self.run_case(key=False); self.assertEqual(d.reason_code,'CREDENTIAL_UNAVAILABLE'); self.assertEqual(c,[]); self.assertEqual(l.state(r.request_id)[0],0)
    def test_endpoints(self):
        for url in ('http://api.openai.com/v1/responses','https://evil.test/v1/responses','https://127.0.0.1/v1/responses','https://api.openai.com:444/v1/responses','https://u:p@api.openai.com/v1/responses'):
            d,c,k,_,_=self.run_case(config={'endpoint':url}); self.assertEqual(d.reason_code,'CONFIG_INVALID'); self.assertEqual(c+k,[])
    def test_model(self): self.assertEqual(self.run_case(config={'model_id':'other'})[0].reason_code,'MODEL_NOT_ALLOWED')
    def test_request_size(self): self.assertEqual(self.run_case(config={'max_request_bytes':1})[0].reason_code,'CONFIG_INVALID')
    def test_response_size(self): self.assertEqual(self.run_case(config={'max_response_bytes':1})[0].reason_code,'RESPONSE_TOO_LARGE')
    def test_output_tokens(self): self.assertEqual(self.run_case(config={'max_output_tokens':101})[0].reason_code,'CONFIG_INVALID')
    def test_budget(self):
        d,c,k,_,_=self.run_case(config={'max_cost_usd':D('0')}); self.assertEqual(d.reason_code,'BUDGET_EXCEEDED'); self.assertEqual(c+k,[])
    def test_reservation_reconcile(self):
        d,_,_,l,r=self.run_case(); self.assertEqual(d.budget_state,'REPORTED_UNSETTLED'); self.assertEqual(l.state(r.request_id)[0],D('.0102')); self.assertEqual(l.state(r.request_id)[2],D('.00004'))
    def test_ambiguous(self):
        for code in ('CONNECT_TIMEOUT','READ_TIMEOUT','TRANSPORT_FAILURE'):
            d,c,_,l,r=self.run_case(error=code); self.assertEqual(d.reason_code,code); self.assertEqual(len(c),1); self.assertEqual(d.budget_state,'UNRESOLVED'); self.assertGreater(l.state(r.request_id)[0],0)
    def test_deadline(self):
        values=iter((0.0,1.0)); d,c,_,_,_=self.run_case(clock=lambda:next(values)); self.assertEqual(d.reason_code,'DEADLINE_EXCEEDED'); self.assertEqual(c,[])
    def test_http_errors(self):
        for status,code in ((302,'PROVIDER_ERROR'),(401,'AUTHENTICATION_FAILED'),(429,'RATE_LIMITED'),(500,'PROVIDER_ERROR')):
            d,c,_,_,_=self.run_case(status=status); self.assertEqual(d.reason_code,code); self.assertEqual(len(c),1)
    def test_no_retry(self): self.assertEqual(self.run_case(config={'max_attempts':2})[1],[])
    def test_tool(self): self.assertEqual(self.run_case(change=lambda e:e['output'][0].update(type='function_call'))[0].reason_code,'RESPONSE_INVALID')
    def test_incomplete(self): self.assertEqual(self.run_case(change=lambda e:e.update(status='incomplete'))[0].reason_code,'RESPONSE_INVALID')
    def test_model_response(self): self.assertEqual(self.run_case(change=lambda e:e.update(model='other'))[0].reason_code,'MODEL_MISMATCH')
    def test_usage(self): self.assertEqual(self.run_case(change=lambda e:e['usage'].update(output_tokens=-1))[0].reason_code,'RESPONSE_INVALID')
    def test_downstream(self):
        d,*_=self.run_case(change=lambda e:e['output'][0]['content'][0].update(text='{}')); self.assertEqual(d.reason_code,'DOWNSTREAM_REJECTED'); self.assertEqual(d.downstream.reason_code,'COG008_FIELDS')
    def test_malformed(self):
        s,r,p,c,price,e=fixture()
        with self.assertRaises(LiveError): parse_response(200,b'{',c,r,price,0)
    def test_invalid_tls(self):
        s,r,p,c,price,e=fixture()
        class Bad: check_hostname=False; verify_mode=0
        with patch('ssl.create_default_context',return_value=Bad()),patch('http.client.HTTPSConnection',side_effect=AssertionError('network')):
            with self.assertRaisesRegex(LiveError,'CONFIG_INVALID'): https_exchange(c,b'{}','synthetic',1,lambda:0)
    def test_redaction(self):
        self.assertEqual(str(LiveError('secret material')),'TRANSPORT_FAILURE')
    def test_integrity(self):
        root=pathlib.Path(__file__).resolve().parent.parent; inv=root/'cog009b-integrity.json'
        if not inv.exists(): self.skipTest('baseline inventory required')
        for f,h in json.loads(inv.read_text()).items(): self.assertEqual(hashlib.sha256((root/f).read_bytes()).hexdigest(),h)

if __name__=='__main__': unittest.main()
