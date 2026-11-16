"""NCI-006 audit tests: pin independently established findings (confirmations AND falsifications).
Run from the reconstructed runtime root: PYTHONPATH=src:<pkg>/eval python3 -m unittest <this file>."""
import unittest, copy, tempfile
from pathlib import Path
from eval_planning import blocks, act, model, reference, simulate
from eval_learning import task as ltask
import random
from skynet_native_planning.core import parse, search
from skynet_native_planning.integration import execute_goal, verify_execution
from skynet_native_learning import ExperienceStore, run_episode
from skynet_native_learning.benchmark import host, REG
from skynet_native_autonomy import run_goal
from skynet_components import ComponentHost
from skynet_sys.capabilities import HostPolicy
from skynet.system import System
def branchy():
    A = [act('s1', ['s'], ['a'], ['s']), act('a1', ['a'], ['b'], ['a']), act('b1', ['b'], ['g'], ['b']), act('s2', ['s'], ['c'], ['s'], cost=2), act('c2', ['c'], ['g'], ['c'], cost=2), act('a3', ['a'], ['c'], ['a'])]
    return model(['s', 'a', 'b', 'c', 'g'], ['s'], ['g'], A)
def T(tid, m, ff=()):
    n = [a['name'] for a in m['actions']]; return {'task_id': tid, 'features': {'risk': 10}, 'model': m, 'strategies': {'fast': n, 'safe': n}, 'faults_by_strategy': {'fast': list(ff), 'safe': []}}
class Planning(unittest.TestCase):
    def test_sussman_optimal_vs_independent_reference(self):
        m = blocks(random.Random(1), 0); r = search(parse(m)).json(); self.assertEqual(simulate(m, r['plan'])[:2], (True, 'OK')); self.assertEqual(r['cost'], reference(m)['cost'])
    def test_cyclic_unreachable(self):
        m = model(['r0', 'r1', 'g'], ['r0'], ['g'], [act('f', ['r0'], ['r1'], ['r0']), act('b', ['r1'], ['r0'], ['r1'])]); self.assertEqual(search(parse(m)).status, 'UNREACHABLE')
    def test_finding_A3_avoid_is_final_state_only(self):
        m = model(['s', 'w', 'g', 'alarm', 'x'], ['s'], ['g'], [act('sw', ['s'], ['w', 'alarm'], ['s']), act('wg', ['w'], ['g'], ['w']), act('quiet', ['alarm'], [], ['alarm']), act('sx', ['s'], ['x'], ['s'], cost=5), act('xg', ['x'], ['g'], ['x'], cost=5)], avoid=['alarm'])
        self.assertIn('sw', search(parse(m)).plan)
class Autonomy(unittest.TestCase):
    def setUp(self): self.d = Path(tempfile.mkdtemp()); self.n = 0
    def store(self): self.n += 1; return ExperienceStore(self.d / ('s%d.json' % self.n))
    def test_denied_host_executes_nothing(self):
        h = ComponentHost(System(1, 1), REG, HostPolicy('d', (('admin', 'cognitive.reason'), ('admin', 'learning.propose'))))
        r = run_goal(h, self.store(), T('x1', branchy())); self.assertEqual((r['status'], r['reason']), ('REJECTED', 'CAPABILITY_DENIED')); self.assertEqual(len(h.receipts), 0)
    def test_replan_from_observed_state(self):
        r = run_goal(host(), self.store(), T('x2', branchy(), [{'attempt': 1, 'kind': 'NO_EFFECT'}])); rd = r['execution']['rounds']
        self.assertTrue(r['verified_goal']); self.assertNotEqual(rd[1]['observed']['state'], rd[0]['observed']['state']); self.assertTrue(rd[1]['observed']['disabled'])
    def test_finding_A4_transient_fault_disables_sole_path(self):
        m = model(['s', 'g'], ['s'], ['g'], [act('only', ['s'], ['g'], ['s'])]); r = run_goal(host(), self.store(), T('x3', m, [{'attempt': 0, 'kind': 'FAIL'}]))
        self.assertFalse(r['verified_goal']); self.assertEqual(r['reason'], 'NO_FEASIBLE_PLAN')
class Evidence(unittest.TestCase):
    def test_tamper_rejected_but_omitted_faults_accepted(self):
        m = branchy(); good = execute_goal(host(), m, run_id='g'); bad = execute_goal(host(), m, run_id='b', faults=[{'attempt': 0, 'kind': 'FAIL'}], max_replans=0)
        t = copy.deepcopy(bad); t['goal_satisfied'] = True; t['status'] = 'SUCCESS'
        with self.assertRaises(ValueError): verify_execution(m, t, [{'attempt': 0, 'kind': 'FAIL'}])
        self.assertTrue(verify_execution(m, good, ()))  # finding E3: trusted host may omit real faults
class Learning(unittest.TestCase):
    def test_adapts_to_inverted_rewards(self):
        s = ExperienceStore(Path(tempfile.mkdtemp()) / 'l.json')
        for i in range(8): run_episode(host(), s, ltask('I:%d' % i, 10 if i % 2 == 0 else 80, i % 2 == 0, 3, 2), split='train')
        self.assertEqual(run_episode(host(), s, ltask('J:0', 20, True, 3, 2))['strategy'], 'safe'); self.assertEqual(run_episode(host(), s, ltask('J:1', 90, False, 3, 2))['strategy'], 'fast')
    def test_unseen_feature_rejected(self):
        from skynet_native_learning import context, LearningError
        with self.assertRaises(LearningError): context({'risk': 1, 'other': 2})
class Qualification(unittest.TestCase):
    def test_level_q1(self):
        from skynet_final_qualification.audit import audit
        from skynet_final_qualification.qualification import run, level
        root = Path(__import__('skynet').__file__).resolve().parents[2]; self.assertEqual(level(audit(root), run(audit(root))), 'Q1')
if __name__ == '__main__': unittest.main()
