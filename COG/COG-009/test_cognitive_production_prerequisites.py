import unittest,tempfile,sqlite3
from pathlib import Path
from cognitive_durable_budget import Ledger,BudgetError
from cognitive_token_accounting import account_tokens
from cognitive_pricing_authority import qualify_pricing
from cognitive_execution_deadline import execute_with_deadline
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/"budget.db")
        self.l=Ledger(self.path); self.l.create_account("test",10)
    def tearDown(self):
        self.l.close();self.tmp.cleanup()
    def reserve(self):
        self.l.reserve("r","s","test",6,1)
    def test_reservation(self):
        self.reserve();self.assertEqual(self.l.read("r").reserved_usd,"0.000006")
    def test_duplicate(self):
        self.reserve()
        with self.assertRaises(BudgetError):self.reserve()
        self.assertEqual(self.l.db.execute("SELECT count(*) FROM audit").fetchone()[0],1)
    def test_overspend_rollback(self):
        self.reserve()
        with self.assertRaisesRegex(BudgetError,"BUDGET_EXCEEDED"):self.l.reserve("r2","s2","test",5,2)
        self.assertEqual(self.l.db.execute("SELECT count(*) FROM reservations").fetchone()[0],1)
    def test_negative(self):
        with self.assertRaises(BudgetError):self.l.reserve("r","s","test",-1,1)
    def test_restart_unresolved(self):
        self.reserve();self.l.mark_unresolved("r",2);self.l.close();self.l=Ledger(self.path)
        self.assertEqual(self.l.read("r").state,"UNRESOLVED")
    def test_idempotent_unresolved(self):
        self.reserve();self.l.mark_unresolved("r",2);self.l.mark_unresolved("r",3)
        self.assertEqual(self.l.db.execute("SELECT count(*) FROM audit").fetchone()[0],2)
    def test_immutable_audit(self):
        self.reserve()
        with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute("DELETE FROM audit")
    def test_no_fake_reconciliation(self):
        self.reserve()
        with self.assertRaises(BudgetError):self.l.reconcile(verified=True)
        with self.assertRaises(BudgetError):self.l.release(verified=True)
        self.assertEqual(self.l.read("r").state,"RESERVED")
    def test_time_regression(self):
        self.reserve()
        with self.assertRaises(BudgetError):self.l.mark_unresolved("r",0)
        self.assertEqual(self.l.read("r").state,"RESERVED")
    def test_token_gate(self):
        with self.assertRaisesRegex(ValueError,"UNVERIFIED"):account_tokens(verified=True)
    def test_price_gate(self):
        with self.assertRaisesRegex(ValueError,"UNAVAILABLE"):qualify_pricing(verified=True)
    def test_deadline_no_dispatch(self):
        def prohibited():raise AssertionError("DISPATCHED")
        with self.assertRaisesRegex(ValueError,"NOT_IMPLEMENTED"):execute_with_deadline(prohibited)
if __name__=="__main__":unittest.main()
