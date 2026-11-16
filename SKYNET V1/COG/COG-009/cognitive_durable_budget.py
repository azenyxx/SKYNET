"""Isolated SQLite liabilities only. No billing authority or production integration."""
from dataclasses import dataclass
import sqlite3

class BudgetError(ValueError):
    pass

@dataclass(frozen=True)
class DurableBudgetLedgerV1:
    request_id: str
    reservation_id: str
    account_id: str
    reserved_usd: str
    reconciled_usd: str
    state: str
    created_at: int
    updated_at: int
    reconciliation_reference: str | None

def integer(value):
    if type(value) is not int or not 0 <= value <= 2**63-1:
        raise BudgetError("INVALID_INTEGER")
    return value

def identifier(value):
    if type(value) is not str or not 1 <= len(value) <= 128 or not all(c.isascii() and (c.isalnum() or c in "_-") for c in value):
        raise BudgetError("INVALID_ID")
    return value

class Ledger:
    """Amounts are integer micro-USD. SQLite is not a protected authority store."""
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=1, isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, ceiling INTEGER NOT NULL CHECK(ceiling>=0));
        CREATE TABLE IF NOT EXISTS reservations(
          request_id TEXT PRIMARY KEY,reservation_id TEXT UNIQUE NOT NULL,
          account_id TEXT NOT NULL REFERENCES accounts(id),amount INTEGER NOT NULL CHECK(amount>0),
          state TEXT NOT NULL CHECK(state IN ('RESERVED','UNRESOLVED')),
          created INTEGER NOT NULL,updated INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY,request_id TEXT NOT NULL REFERENCES reservations(request_id),
          old_state TEXT,new_state TEXT NOT NULL,at INTEGER NOT NULL);
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
        """)
    def close(self):
        self.db.close()
    def create_account(self, account, ceiling):
        identifier(account);integer(ceiling)
        try:
            self.db.execute("INSERT INTO accounts VALUES (?,?)",(account,ceiling))
        except sqlite3.IntegrityError:
            raise BudgetError("ACCOUNT_CONFLICT") from None
    def reserve(self, request, reservation, account, amount, now):
        for v in (request,reservation,account): identifier(v)
        integer(amount);integer(now)
        if amount == 0: raise BudgetError("INVALID_AMOUNT")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT ceiling FROM accounts WHERE id=?",(account,)).fetchone()
            if row is None: raise BudgetError("UNKNOWN_ACCOUNT")
            # Python sum avoids SQLite integer SUM overflow.
            used=sum(r[0] for r in self.db.execute("SELECT amount FROM reservations WHERE account_id=?",(account,)))
            if amount > row[0]-used: raise BudgetError("BUDGET_EXCEEDED")
            self.db.execute("INSERT INTO reservations VALUES (?,?,?,?,?,?,?)",(request,reservation,account,amount,"RESERVED",now,now))
            self.db.execute("INSERT INTO audit(request_id,old_state,new_state,at) VALUES (?,NULL,'RESERVED',?)",(request,now))
            self.db.execute("COMMIT")
        except Exception as e:
            self.db.execute("ROLLBACK")
            if isinstance(e,sqlite3.IntegrityError): raise BudgetError("DUPLICATE_RESERVATION") from None
            raise
    def mark_unresolved(self, request, now):
        identifier(request);integer(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT state,updated FROM reservations WHERE request_id=?",(request,)).fetchone()
            if row is None: raise BudgetError("UNKNOWN_REQUEST")
            if now < row[1]: raise BudgetError("TIME_REGRESSION")
            if row[0]=="RESERVED":
                self.db.execute("UPDATE reservations SET state='UNRESOLVED',updated=? WHERE request_id=?",(now,request))
                self.db.execute("INSERT INTO audit(request_id,old_state,new_state,at) VALUES (?,'RESERVED','UNRESOLVED',?)",(request,now))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def read(self, request):
        identifier(request)
        row=self.db.execute("SELECT * FROM reservations WHERE request_id=?",(request,)).fetchone()
        if row is None: raise BudgetError("UNKNOWN_REQUEST")
        amount=f"{row[3]//1000000}.{row[3]%1000000:06d}"
        return DurableBudgetLedgerV1(row[0],row[1],row[2],amount,"0.000000",row[4],row[5],row[6],None)
    def reconcile(self, *args, **kwargs):
        raise BudgetError("TRUSTED_RECONCILIATION_UNAVAILABLE")
    def release(self, *args, **kwargs):
        raise BudgetError("TRUSTED_RELEASE_UNAVAILABLE")
