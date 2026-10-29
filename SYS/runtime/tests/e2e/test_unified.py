import unittest,json,os
from pathlib import Path
from skynet.system import System,workload
class UnifiedTests(unittest.TestCase):
 def test_workload(self):
  e=workload();self.assertEqual(e['state_digest'],e['replay_digest']);self.assertEqual((e['tasks'],e['workers'],e['verification_requests'],e['faults']),(20,10,10,5));self.assertGreaterEqual(e['retries'],2);self.assertEqual(len(e['restorations']),2);self.assertGreaterEqual(len(e['stale_rejections']),2);(Path(os.environ['SKYNET_EVIDENCE_OUT']).write_text(json.dumps(e,indent=2)) if os.environ.get('SKYNET_EVIDENCE_OUT') else None)  # AUDIT D-001: never mutate checksummed audit/ evidence implicitly;print('UNIFIED_WORKLOAD '+json.dumps(e))
 def test_initialization(self):
  h=System();self.assertIs(h.recovery.coordinator.workers,h.workers);self.assertIs(h.restorer.store,h.memory);self.assertEqual(len(h.identities),12);self.assertEqual(len(h.engine.policies),3)
 def test_unknown_operation(self):
  h=System(1,1);before=h.state_digest()
  with self.assertRaisesRegex(ValueError,'^ValueError:OPERATION$'):h.run('shell')
  self.assertEqual(before,h.state_digest())
