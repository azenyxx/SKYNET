"""Worker deadline execution is deliberately unavailable in this checkpoint."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionDeadlinePolicyV1:
    request_id: str
    total_deadline_ms: int
    connect_timeout_ms: int
    read_timeout_ms: int
    cancellation_strategy: str
    worker_termination_grace_ms: int
def execute_with_deadline(*args, **kwargs):
    raise ValueError("HARD_DEADLINE_NOT_IMPLEMENTED")
