"""Endpoint restrictions and explicitly single-thread/process, non-durable test ledger."""
from decimal import Decimal
import os
import threading
from cognitive_live_provider_contracts import *

ENDPOINT='https://api.openai.com/v1/responses'
def validate_config(c,p):
    check(type(c) is LiveProviderConfigV1 and type(p) is PricePolicyV1)
    check(c.provider_id=='openai','PROVIDER_NOT_ALLOWED')
    check(type(c.model_id) is str and 1<=len(c.model_id)<=64)
    check(c.endpoint==ENDPOINT and c.allowed_hostnames==('api.openai.com',))
    check(type(c.network_enabled) is bool)
    check(type(p.allowed_models) is tuple and 1<=len(p.allowed_models)<=64 and all(type(x) is str for x in p.allowed_models))
    check(c.model_id in p.allowed_models,'MODEL_NOT_ALLOWED')
    check(type(p.version) is str and 1<=len(p.version)<=128 and c.price_table_version==p.version)
    check(money(c.max_cost_usd) and money(p.input_usd_per_token) and money(p.output_usd_per_token))
    for name in ('connect_timeout_ms','read_timeout_ms','total_deadline_ms','max_request_bytes','max_response_bytes','max_output_tokens','max_attempts'):
        check(integer(getattr(c,name)) and getattr(c,name)>0)
    check(c.max_attempts==1 and c.max_request_bytes<=65536 and c.max_response_bytes<=1048576)
    check(integer(p.input_token_bound) and p.input_token_bound>0)

class IsolatedBudgetLedger:
    """Reject cross-thread/process access. Not an operational or durable budget authority."""
    def __init__(self,limit,*,isolated_single_process=False):
        check(isolated_single_process is True and money(limit))
        self._owner=(os.getpid(),threading.get_ident()); self._limit=limit; self._records={}
    def _guard(self): check(self._owner==(os.getpid(),threading.get_ident()))
    def reserve(self,key,amount):
        self._guard(); check(money(amount))
        check(key not in self._records and sum(x[0] for x in self._records.values())+amount<=self._limit,'BUDGET_EXCEEDED')
        self._records[key]=(amount,'RESERVED',None)
    def release_unsent(self,key):
        self._guard(); amount,state,actual=self._records[key]; check(state=='RESERVED'); self._records[key]=(Decimal(0),'UNSENT_RELEASED',None)
    def unresolved(self,key):
        self._guard(); amount,_,actual=self._records[key]; self._records[key]=(amount,'UNRESOLVED',actual)
    def reconcile(self,key,estimate):
        self._guard(); amount,state,_=self._records[key]; check(money(estimate) and estimate<=amount,'BUDGET_EXCEEDED')
        # Reported usage is not an invoice: keep the full liability until external settlement.
        self._records[key]=(amount,'REPORTED_UNSETTLED',estimate)
    def state(self,key):
        self._guard(); return self._records.get(key,(Decimal(0),'NONE',None))
