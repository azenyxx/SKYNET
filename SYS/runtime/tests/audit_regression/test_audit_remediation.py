"""SKYNET-FINAL-AUDIT-001 regression and negative tests for D-001 and D-002."""
import unittest,subprocess,sys,os,hashlib,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(code,paths,cwd):
 env=dict(os.environ,PYTHONPATH=os.pathsep.join(str(x) for x in paths),PYTHONDONTWRITEBYTECODE='1');env.pop('SKYNET_EVIDENCE_OUT',None)
 return subprocess.run([sys.executable,'-c',code],cwd=cwd,env=env,capture_output=True,text=True,timeout=240)
class D001EvidenceImmutability(unittest.TestCase):
 def test_unified_workload_does_not_mutate_audit_evidence(self):
  target=ROOT/'audit'/'WORKLOAD-EVIDENCE.json';before=sha(target)
  p=run("import unittest,sys;sys.path.insert(0,'tests/e2e');import test_unified as t;r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(t.UnifiedTests));sys.exit(not r.wasSuccessful())",[ROOT/'src'],ROOT)
  self.assertEqual(p.returncode,0,p.stderr[-800:]);self.assertEqual(sha(target),before)
 def test_explicit_evidence_output_still_supported(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'w.json';env_code="import os,sys,unittest;os.environ['SKYNET_EVIDENCE_OUT']=%r;sys.path.insert(0,'tests/e2e');import test_unified as t;r=unittest.TextTestRunner().run(t.UnifiedTests('test_workload'));sys.exit(not r.wasSuccessful())"%str(out)
   p=run(env_code,[ROOT/'src'],ROOT);self.assertEqual(p.returncode,0,p.stderr[-800:])
   e=json.loads(out.read_text());self.assertEqual(e['state_digest'],e['replay_digest']);self.assertEqual(e['tasks'],20)
 def test_cwd_independent(self):
  with tempfile.TemporaryDirectory() as d:
   p=run("import sys,unittest;sys.path.insert(0,%r);import test_unified as t;r=unittest.TextTestRunner().run(t.UnifiedTests('test_workload'));sys.exit(not r.wasSuccessful())"%str(ROOT/'tests'/'e2e'),[ROOT/'src'],d)
   self.assertEqual(p.returncode,0,p.stderr[-800:]);self.assertFalse((Path(d)/'audit').exists())
class D002IntegrationImport(unittest.TestCase):
 def test_imports_with_documented_pythonpath(self):
  p=run("import skynet_sys_integration as m;print(m.Harness.__name__)",[ROOT/'src'],ROOT);self.assertEqual(p.returncode,0,p.stderr[-800:])
 def test_negative_fixture_dependent_call_fails_explicitly(self):
  # Harness.run() reaches integrated()/engine(); harness.workload() is fixture-free and must still work.
  code="import skynet_sys_integration.harness as h\nfor n in ('integrated','engine','IntegrationTests','payload','assessment'):\n try:getattr(h,n)();print('ACCEPTED',n)\n except h.IntegrationError as e:print('CODE',n,e)\nprint('WORKLOAD',type(h.workload()).__name__)"
  p=run(code,[ROOT/'src'],ROOT)
  for n in ('integrated','engine','IntegrationTests','payload','assessment'):self.assertIn('CODE %s TEST_FIXTURES_UNAVAILABLE'%n,p.stdout,p.stderr[-800:])
  self.assertIn('WORKLOAD dict',p.stdout)
 def test_fixture_path_behavior_unchanged(self):
  p=run("import skynet_sys_integration.harness as h;import test_workers;assert h.integrated is test_workers.integrated;print('SAME')",[ROOT/'src',ROOT/'tests/unit/sys005',ROOT/'tests/unit/sys006'],ROOT)
  self.assertIn('SAME',p.stdout,p.stderr[-800:])
if __name__=='__main__':unittest.main()
