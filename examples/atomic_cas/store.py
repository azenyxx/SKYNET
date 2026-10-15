"""Public, standalone SQLite CAS example. NOT a SKYNET authority implementation."""
from dataclasses import dataclass
from hashlib import sha256
import json
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS heads (
  entity_id TEXT PRIMARY KEY,
  revision INTEGER NOT NULL CHECK(revision >= 0),
  status TEXT NOT NULL CHECK(status IN ('ACTIVE','REVOKED'))
);
CREATE TABLE IF NOT EXISTS receipts (
  operation_id TEXT PRIMARY KEY,
  nonce TEXT NOT NULL UNIQUE,
  entity_id TEXT NOT NULL REFERENCES heads(entity_id),
  request_digest TEXT NOT NULL,
  old_revision INTEGER NOT NULL,
  new_revision INTEGER NOT NULL,
  result TEXT NOT NULL CHECK(result='REVOKED')
);
CREATE TABLE IF NOT EXISTS audit (
  operation_id TEXT PRIMARY KEY REFERENCES receipts(operation_id),
  event TEXT NOT NULL CHECK(event='REVOKE')
);
"""

class Conflict(Exception):
    pass

@dataclass(frozen=True)
class Revoke:
    entity_id: str
    expected_revision: int
    operation_id: str
    nonce: str


def digest(req: Revoke) -> str:
    payload = json.dumps(vars(req), sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return sha256(b'public-atomic-cas-demo:v1\x00' + payload.encode('ascii')).hexdigest()


def initialize(path: str | Path, entity_id: str = 'example') -> None:
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.execute('INSERT OR IGNORE INTO heads VALUES (?,0,?)', (entity_id, 'ACTIVE'))


def revoke(path: str | Path, req: Revoke, *, fail_before_commit: bool = False) -> tuple:
    """Atomic, idempotent synthetic revocation. No authorization or crypto signature checks."""
    if type(req) is not Revoke or not all(type(x) is str and x for x in (req.entity_id, req.operation_id, req.nonce)) or type(req.expected_revision) is not int or req.expected_revision < 0:
        raise ValueError('invalid request')
    db = sqlite3.connect(path, timeout=5, isolation_level=None)
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        h = digest(req)
        existing = db.execute('SELECT operation_id,nonce,entity_id,request_digest,old_revision,new_revision,result FROM receipts WHERE operation_id=?', (req.operation_id,)).fetchone()
        if existing:
            if existing[1] == req.nonce and existing[2] == req.entity_id and existing[3] == h:
                db.execute('COMMIT')
                return existing
            raise Conflict('OPERATION_CONFLICT')
        if db.execute('SELECT 1 FROM receipts WHERE nonce=?', (req.nonce,)).fetchone():
            raise Conflict('NONCE_CONFLICT')
        cur = db.execute("UPDATE heads SET revision=revision+1,status='REVOKED' WHERE entity_id=? AND revision=? AND status='ACTIVE'", (req.entity_id, req.expected_revision))
        if cur.rowcount != 1:
            raise Conflict('CAS_CONFLICT')
        db.execute('INSERT INTO receipts VALUES (?,?,?,?,?,?,?)', (req.operation_id, req.nonce, req.entity_id, h, req.expected_revision, req.expected_revision+1, 'REVOKED'))
        db.execute('INSERT INTO audit VALUES (?,?)', (req.operation_id, 'REVOKE'))
        if fail_before_commit:
            raise RuntimeError('injected failure')
        db.execute('COMMIT')
        return (req.operation_id, req.nonce, req.entity_id, h, req.expected_revision, req.expected_revision+1, 'REVOKED')
    except BaseException:
        if db.in_transaction:
            db.execute('ROLLBACK')
        raise
    finally:
        db.close()
