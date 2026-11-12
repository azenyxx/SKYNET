from meta_test_helpers import *
from cognitive_meta_uncertainty import calibration,assess_uncertainty
from cognitive_meta_monitor import monitor
class UncertaintyTests(unittest.TestCase):
 def test_exact_metrics(self):
  c=calibration((0,1000,500,None),(0,1,1,0));self.assertEqual((c.brier_numerator,c.brier_denominator),(1,12));self.assertEqual((c.ece_numerator,c.ece_denominator),(1,6));self.assertEqual((c.covered,c.total),(3,4));self.assertEqual(c.calibration_status,'SYNTHETIC_FIXTURE_ONLY')
 def test_invalid_probability(self):
  with self.assertRaises(MetaContractError):calibration((float('nan'),),(1,))
 def test_conflict(self):t=trace(change=('WORLD','CONFLICT'));self.assertEqual(assess_uncertainty(t,monitor(t,budget())).classification,'CONTRADICTED')
