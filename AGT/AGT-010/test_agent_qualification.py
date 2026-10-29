import unittest
from dataclasses import replace, FrozenInstanceError
import agent_qualification as q
import test_agent_recovery as rf
import test_agent_supervision as sf


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.components = tuple(q.make(q.ComponentDescriptor, component_id=k,
            capabilities=('diagnostic',), interfaces=('evaluate',), dependencies=deps)
            for k, deps in (('AGT003', ()), ('AGT006', ('AGT003',)),
                            ('AGT007', ('AGT006',)), ('AGT008', ('AGT007',)), ('AGT009', ('AGT008',))))
        self.findings = q.inherited_findings()
        self.policy = q.make(q.QualificationPolicy, policy_id='local', minimum_evidence=1,
                             permitted_verdicts=q.STATUSES, resource_ceiling=32)
        self.previous = q.initial(self.policy)
        self.evidence = (q.make(q.QualificationEvidence, evidence_id='diagnostic', component_id='AGT003',
            evidence_type='STATIC', source_commitment='a'*64, observed_result='PASS', verification_status='NOT_ESTABLISHED'),)

    def run_assessment(self, **changes):
        options = dict(expected_state=self.previous.commitment,
                       expected_snapshot=q.digest((self.components, (), self.findings)),
                       expected_policy=self.policy.commitment,
                       approved_evidence=tuple(e.commitment for e in self.evidence), sequence=self.previous.consumed + 1)
        options.update(changes)
        return q.assess(self.components, (), self.evidence, self.findings, self.policy, self.previous, **options)

    def test_commitment_mismatch(self):
        with self.assertRaises(ValueError):
            replace(self.policy, commitment='0'*64)

    def test_version(self):
        with self.assertRaises(ValueError):
            replace(self.policy, version='wrong')

    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.policy.resource_ceiling = 99

    def test_unknown_field(self):
        with self.assertRaises(TypeError):
            q.ComponentDescriptor(unknown=True)

    def test_boolean_budget(self):
        with self.assertRaises(ValueError):
            q.make(q.QualificationPolicy, policy_id='bad', minimum_evidence=1,
                   permitted_verdicts=q.STATUSES, resource_ceiling=True)

    def test_negative_budget(self):
        with self.assertRaises(ValueError):
            q.make(q.QualificationPolicy, policy_id='bad', minimum_evidence=1,
                   permitted_verdicts=q.STATUSES, resource_ceiling=-1)

    def test_order(self):
        self.assertEqual(q.graph(self.components, ())[0][0], 'AGT003')

    def test_duplicate_component(self):
        with self.assertRaises(ValueError):
            q.graph(self.components + self.components[:1], ())

    def test_unknown_dependency(self):
        c = q.make(q.ComponentDescriptor, component_id='X', capabilities=(), interfaces=(), dependencies=('missing',))
        with self.assertRaises(ValueError):
            q.graph((c,), ())

    def test_cycle(self):
        c = q.make(q.ComponentDescriptor, component_id='X', capabilities=(), interfaces=(), dependencies=('X',))
        with self.assertRaises(ValueError):
            q.graph((c,), ())

    def test_unsupported_interface(self):
        edge = q.make(q.IntegrationDependency, source_id='AGT006', target_id='AGT003',
                      required_interface='missing', qualification_requirement='QUALIFIED_LOCAL')
        with self.assertRaises(ValueError):
            q.graph(self.components, (edge,))

    def test_unknown_edge(self):
        edge = q.make(q.IntegrationDependency, source_id='missing', target_id='AGT003',
                      required_interface='evaluate', qualification_requirement='QUALIFIED_LOCAL')
        with self.assertRaises(ValueError):
            q.graph(self.components, (edge,))

    def test_unpinned_evidence(self):
        with self.assertRaises(ValueError):
            self.run_assessment(approved_evidence=())

    def test_duplicate_evidence(self):
        self.evidence *= 2
        with self.assertRaises(ValueError):
            self.run_assessment()

    def test_false_pass_agt009(self):
        self.evidence = (q.make(q.QualificationEvidence, evidence_id='forged', component_id='AGT009',
            evidence_type='REPRODUCED', source_commitment='a'*64, observed_result='PASS', verification_status='NOT_ESTABLISHED'),)
        with self.assertRaisesRegex(ValueError, 'FALSE_PASS_AGT009'):
            self.run_assessment()

    def test_no_full_promotion(self):
        self.assertNotIn('QUALIFIED_LOCAL', dict(self.run_assessment()[2].component_statuses).values())

    def test_debt_suppression(self):
        self.findings = self.findings[:-1]
        with self.assertRaises(ValueError):
            self.run_assessment()

    def test_open_p1_no_closure(self):
        with self.assertRaises(ValueError):
            replace(self.findings[0], status='CLOSED')

    def test_blocking_propagates(self):
        self.assertEqual(dict(self.run_assessment()[2].component_statuses)['AGT009'], 'BLOCKED')

    def test_preserves_cog_debt(self):
        self.assertIn('C20-001', self.run_assessment()[0].unresolved_findings)

    def test_stale_state(self):
        with self.assertRaises(ValueError):
            self.run_assessment(expected_state='0'*64)

    def test_sequence(self):
        with self.assertRaises(ValueError):
            self.run_assessment(sequence=2)

    def test_stop(self):
        with self.assertRaises(ValueError):
            self.run_assessment(stop=True)

    def test_deadline(self):
        with self.assertRaises(ValueError):
            self.run_assessment(now=1, deadline=1)

    def test_budget_conservation(self):
        state = self.run_assessment()[0]
        self.assertEqual(state.consumed + state.remaining, 32)

    def test_replay(self):
        self.previous = self.run_assessment()[0]
        with self.assertRaises(ValueError):
            self.run_assessment()

    def test_determinism(self):
        self.assertEqual(self.run_assessment(), self.run_assessment())

    def test_atomic_rejection(self):
        before = self.previous
        with self.assertRaises(ValueError):
            self.run_assessment(stop=True)
        self.assertEqual(before, self.previous)

    def test_no_production(self):
        self.assertFalse(self.run_assessment()[2].production_authorized)

    def test_no_knowledge(self):
        self.assertFalse(self.run_assessment()[2].knowledge_promotion_authorized)

    def test_real_recovery(self):
        args = rf.fixture()
        self.assertEqual(rf.r.coordinate(*args)[2].execution_status, 'COORDINATION_RECORDED')

    def test_real_feedback(self):
        args = rf.fixture()
        self.assertEqual(rf.f.evaluate(*args[0])[-1].decision_status, 'ESCALATE')

    def test_real_planning(self):
        args = rf.fixture()
        self.assertEqual(args[0][4][0].consumed_budget, 3)

    def test_real_governance(self):
        args = rf.fixture()
        self.assertEqual(args[0][4][2][1].task_outcomes[0].execution_status, 'FAILED')

    def test_real_supervision_failure(self):
        fixture = sf.SupervisionTests()
        fixture.setUp()
        with self.assertRaisesRegex(TypeError, 'tuple indices'):
            fixture.invoke()


if __name__ == '__main__':
    unittest.main()
