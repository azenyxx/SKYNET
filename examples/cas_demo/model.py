"""Synthetic immutable CAS and replay demo.

Not a SKYNET authority implementation. No cryptographic verification,
credential management, distributed persistence or production interfaces.
"""
from dataclasses import dataclass, replace
from hashlib import sha256


class Rejected(ValueError):
    """Invalid or conflicting request; state remains unchanged."""


@dataclass(frozen=True)
class Command:
    operation_id: str
    expected_revision: int
    payload: bytes


@dataclass(frozen=True)
class Receipt:
    operation_id: str
    payload_digest: str
    revision: int


@dataclass(frozen=True)
class Snapshot:
    revision: int
    value: bytes
    receipts: tuple[Receipt, ...] = ()


def apply(snapshot: Snapshot, command: Command) -> tuple[Snapshot, Receipt]:
    """Pure CAS: return a new snapshot and receipt or raise Rejected.

    Receipt lookup is illustrative, NOT an authorization mechanism.
    No atomic persistence across processes is provided.
    """
    if not isinstance(command.operation_id, str) or not command.operation_id:
        raise Rejected("invalid operation id")
    if not isinstance(command.payload, bytes):
        raise Rejected("invalid payload")
    if not isinstance(command.expected_revision, int) or isinstance(command.expected_revision, bool):
        raise Rejected("invalid expected revision")
    if not isinstance(snapshot.revision, int) or isinstance(snapshot.revision, bool):
        raise Rejected("invalid state revision")
    if command.expected_revision < 0 or snapshot.revision < 0:
        raise Rejected("negative revision")

    digest = sha256(command.payload).hexdigest()
    for previous in snapshot.receipts:
        if previous.operation_id == command.operation_id:
            if previous.payload_digest != digest or command.expected_revision != previous.revision - 1:
                raise Rejected("operation conflict")
            return snapshot, previous

    if command.expected_revision != snapshot.revision:
        raise Rejected("stale revision")
    if snapshot.revision >= (1 << 63) - 1:
        raise Rejected("revision overflow")

    receipt = Receipt(command.operation_id, digest, snapshot.revision + 1)
    return replace(
        snapshot,
        revision=snapshot.revision + 1,
        value=command.payload,
        receipts=snapshot.receipts + (receipt,),
    ), receipt
