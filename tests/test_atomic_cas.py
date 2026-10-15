import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from examples.atomic_cas.store import Conflict, Revoke, initialize, revoke

class AtomicCASTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'test.sqlite'
        initialize(self.path)
        self.req = Revoke('example', 0, 'operation-1', 'nonce-1')

    def rows(self):
        with sqlite3.connect(self.path) as db:
            return tuple(tuple(db.execute('SELECT * FROM '+t)) for t in ('heads','receipts','audit'))

    def test_commit(self):
        receipt = revoke(self.path, self.req)
        self.assertEqual(receipt[-2:], (1,'REVOKED'))
        self.assertEqual(tuple(map(len,self.rows())), (1,1,1))

    def test_exact_replay(self):
        first = revoke(self.path,self.req)
        self.assertEqual(first,revoke(self.path,self.req))
        self.assertEqual(tuple(map(len,self.rows())), (1,1,1))

    def test_changed_operation(self):
        revoke(self.path,self.req)
        with self.assertRaisesRegex(Conflict,'OPERATION_CONFLICT'):
            revoke(self.path,Revoke('example',0,'operation-1','nonce-2'))

    def test_nonce_conflict(self):
        revoke(self.path,self.req)
        with self.assertRaisesRegex(Conflict,'NONCE_CONFLICT'):
            revoke(self.path,Revoke('example',0,'operation-2','nonce-1'))

    def test_stale_revision(self):
        revoke(self.path,self.req)
        with self.assertRaisesRegex(Conflict,'CAS_CONFLICT'):
            revoke(self.path,Revoke('example',0,'operation-2','nonce-2'))

    def test_rollback(self):
        before=self.rows()
        with self.assertRaisesRegex(RuntimeError,'injected failure'):
            revoke(self.path,self.req,fail_before_commit=True)
        self.assertEqual(before,self.rows())
        revoke(self.path,self.req)

    def test_concurrent_competitors(self):
        second=Revoke('example',0,'operation-2','nonce-2')
        def run(r):
            try: return revoke(self.path,r)
            except Conflict as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(run,(self.req,second)))
        self.assertEqual(sum(isinstance(x,tuple) for x in result),1)
        self.assertIn('CAS_CONFLICT',result)
        self.assertEqual(tuple(map(len,self.rows())),(1,1,1))

    def test_reopen(self):
        revoke(self.path,self.req)
        self.assertEqual(self.rows()[0][0],('example',1,'REVOKED'))

if __name__ == '__main__': unittest.main()
