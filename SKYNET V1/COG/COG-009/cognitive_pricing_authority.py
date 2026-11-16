"""No pinned pricing authority available; all qualification denied."""
from dataclasses import dataclass
@dataclass(frozen=True)
class PricingAuthoritySnapshotV1:
    provider_id: str
    model_id: str
    currency: str
    input_price_per_million_tokens: str
    output_price_per_million_tokens: str
    effective_at: str
    retrieved_at: str
    source_identifier: str
    snapshot_sha256: str
    verification_status: str
def qualify_pricing(*args, **kwargs):
    raise ValueError("PRICING_AUTHORITY_UNAVAILABLE")
