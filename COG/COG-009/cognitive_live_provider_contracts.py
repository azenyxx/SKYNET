"""Isolated live configuration; no credentials are represented by these DTOs."""
from dataclasses import dataclass
from decimal import Decimal

CODES=frozenset('NETWORK_DISABLED CONFIG_INVALID PROVIDER_NOT_ALLOWED MODEL_NOT_ALLOWED CREDENTIAL_UNAVAILABLE BUDGET_EXCEEDED CONNECT_TIMEOUT READ_TIMEOUT DEADLINE_EXCEEDED TRANSPORT_FAILURE AUTHENTICATION_FAILED RATE_LIMITED PROVIDER_ERROR RESPONSE_TOO_LARGE RESPONSE_INVALID MODEL_MISMATCH DOWNSTREAM_REJECTED'.split())
class LiveError(ValueError):
    def __init__(self,code):
        self.code=code if code in CODES else 'TRANSPORT_FAILURE'
        super().__init__(self.code)
def check(ok,code='CONFIG_INVALID'):
    if not ok: raise LiveError(code)
def integer(v): return type(v) is int and 0<=v<=2**63-1
def money(v): return type(v) is Decimal and v.is_finite() and Decimal(0)<=v<=Decimal('1000000')

@dataclass(frozen=True)
class LiveProviderConfigV1:
    provider_id: str
    model_id: str
    endpoint: str
    connect_timeout_ms: int
    read_timeout_ms: int
    total_deadline_ms: int
    max_request_bytes: int
    max_response_bytes: int
    max_output_tokens: int
    max_attempts: int
    max_cost_usd: Decimal
    allowed_hostnames: tuple[str,...]
    price_table_version: str
    network_enabled: bool=False

@dataclass(frozen=True)
class PricePolicyV1:
    version: str
    allowed_models: tuple[str,...]
    input_usd_per_token: Decimal
    output_usd_per_token: Decimal
    # Trusted caller bound; no tokenizer or current price assertion supplied by this module.
    input_token_bound: int

@dataclass(frozen=True)
class LiveResultV1:
    reason_code: str
    downstream: object | None
    http_attempts: int
    budget_state: str
    @property
    def executable(self): return False
    @property
    def production_authorized(self): return False
