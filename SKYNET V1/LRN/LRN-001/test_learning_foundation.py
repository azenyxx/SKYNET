import unittest
from dataclasses import replace, fields, FrozenInstanceError
import learning_foundation as l
import test_agent_governance as gf
import test_agent_recovery as rf
import test_agent_qualification as qf


def changed(obj, **changes):
    values = {f.name: getattr(obj, f.name) for f in fields(obj) if f.name != 'commitment'}
    values.update(changes)
    return l.make(type(obj), **values)


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.policy = l.make(l.LearningPolicy, policy_id='local', allowed_evidence_classes=l.CLASSES,
                             minimum_verification='VERIFIED_LOCAL', max_processing_budget=8,
                             promotion_restrictions=('NO_TRAINING','NO_PROMOTION','NO_PRODUCTION'))
        self.state = l.initial(self.policy)
        self.record = l.make(l.ExperienceRecord, experience_id='experience', agent_id='agent', task_id='A',
                             goal_id='goal', workflow_id='workflow', sequence=1,
                             action_category='GOVERNANCE_DIAGNOSTIC', reported_outcome='COMPLETED',
                             source_evidence_commitment='a'*64)
        self.evidence = l.make(l.OutcomeEvidence, evidence_id='evidence', experience_id='experience',
                               observed_result='COMPLETED', verification_level='REPORTED_ONLY',
                               provenance_ref='reported-source', confidence_metadata=(1,2))

    def invoke(self, **options):
        kwargs = dict(expected_state=self.state.commitment, expected_policy=self.policy.commitment,
                      approved_input=l.digest((self.record,self.evidence)))
        kwargs.update(options)
        return l.process(self.record,self.evidence,self.policy,self.state,**kwargs)

    def originals(self, bad=False):
        args = tuple(gf.fixture(bad=bad))
        result = l.memory.gov.govern(*args)
        item = l.memory.ingest_governance(args,result)[0]
        self.record = changed(self.record,workflow_id=args[0],reported_outcome=item.execution_status,
                              source_evidence_commitment=l.source_commitment(args,result))
        self.evidence = changed(self.evidence,observed_result=item.execution_status,
                                verification_level='PARTIALLY_VERIFIED',provenance_ref=item.experience_id)
        return args,result

    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.record.sequence = 2

    def test_commitment(self):
        with self.assertRaises(ValueError):
            replace(self.record,commitment='0'*64)

    def test_version(self):
        with self.assertRaises(ValueError):
            changed(self.record,version='bad')

    def test_identifier(self):
        with self.assertRaises(ValueError):
            changed(self.record,agent_id='../bad')

    def test_bool_sequence(self):
        with self.assertRaises(ValueError):
            changed(self.record,sequence=True)

    def test_confidence_nan(self):
        with self.assertRaises(ValueError):
            changed(self.evidence,confidence_metadata=(float('nan'),1))

    def test_confidence_overflow(self):
        with self.assertRaises(ValueError):
            changed(self.evidence,confidence_metadata=(2,1))

    def test_reported_remains_reported(self):
        self.assertEqual(self.invoke()[1].evidence_validity,'REPORTED_ONLY')

    def test_unavailable(self):
        self.evidence = changed(self.evidence,verification_level='UNAVAILABLE')
        self.assertEqual(self.invoke()[1].eligibility_status,'NOT_QUALIFIED')

    def test_not_established(self):
        self.evidence = changed(self.evidence,verification_level='NOT_ESTABLISHED')
        self.assertEqual(self.invoke()[1].evidence_validity,'NOT_ESTABLISHED')

    def test_missing_provenance(self):
        self.evidence = changed(self.evidence,provenance_ref='')
        self.assertEqual(self.invoke()[1].eligibility_status,'BLOCKED')

    def test_contradicted(self):
        self.evidence = changed(self.evidence,verification_level='CONTRADICTED')
        self.assertEqual(self.invoke()[1].eligibility_status,'REJECTED')

    def test_false_verified(self):
        self.evidence = changed(self.evidence,verification_level='VERIFIED_LOCAL')
        with self.assertRaises(ValueError):
            self.invoke()

    def test_partial_requires_originals(self):
        self.evidence = changed(self.evidence,verification_level='PARTIALLY_VERIFIED')
        with self.assertRaises(ValueError):
            self.invoke()

    def test_experience_binding(self):
        self.evidence = changed(self.evidence,experience_id='other')
        with self.assertRaises(ValueError):
            self.invoke()

    def test_no_candidate_issued(self):
        self.assertEqual(self.invoke()[0].candidate_refs,())

    def test_no_qualified_acceptance(self):
        self.assertEqual(self.invoke()[0].accepted_evidence_refs,())

    def test_rejection_recorded(self):
        self.assertEqual(self.invoke()[0].rejected_evidence_refs,('evidence',))

    def test_attribution_unknown_without_originals(self):
        self.assertEqual(self.invoke()[2].outcome_attribution,'UNKNOWN')

    def test_confidence_unchanged(self):
        before = self.evidence.confidence_metadata
        self.invoke()
        self.assertEqual(self.evidence.confidence_metadata,before)

    def test_deterministic(self):
        self.assertEqual(self.invoke(),self.invoke())

    def test_sequence(self):
        self.record = changed(self.record,sequence=2)
        with self.assertRaises(ValueError):
            self.invoke()

    def test_stale(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_state='0'*64)

    def test_duplicate_experience(self):
        self.state = self.invoke()[0]
        with self.assertRaises(ValueError):
            self.invoke()

    def test_source_replay_different_id(self):
        self.state = self.invoke()[0]
        self.record = changed(self.record,experience_id='second',sequence=2)
        self.evidence = changed(self.evidence,experience_id='second',evidence_id='second')
        with self.assertRaisesRegex(ValueError,'SOURCE_REPLAY'):
            self.invoke()

    def test_cumulative_accounting(self):
        self.state = self.invoke()[0]
        self.record = changed(self.record,experience_id='second',sequence=2,source_evidence_commitment='b'*64)
        self.evidence = changed(self.evidence,experience_id='second',evidence_id='second')
        state = self.invoke()[0]
        self.assertEqual((state.consumed,state.remaining),(2,6))

    def test_budget_escalation(self):
        self.state = changed(self.state,remaining=9)
        with self.assertRaises(ValueError):
            self.invoke()

    def test_policy_swap(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_policy='0'*64)

    def test_input_pin(self):
        with self.assertRaises(ValueError):
            self.invoke(approved_input='0'*64)

    def test_stop(self):
        with self.assertRaises(ValueError):
            self.invoke(stop=True)

    def test_deadline(self):
        with self.assertRaises(ValueError):
            self.invoke(now=1,deadline=1)

    def test_atomic_rejection(self):
        old = self.state
        with self.assertRaises(ValueError):
            self.invoke(stop=True)
        self.assertEqual(old,self.state)

    def test_model_update_denied(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[3],model_update_authorized=True)

    def test_promotion_denied(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[3],knowledge_promotion_authorized=True)

    def test_production_denied(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[3],production_authorized=True)

    def test_real_governance_memory(self):
        original = self.originals()
        self.assertEqual(self.invoke(originals=original)[1].evidence_validity,'PARTIALLY_VERIFIED')

    def test_real_failure_preserved(self):
        original = self.originals(bad=True)
        self.assertEqual(self.invoke(originals=original)[2].outcome_attribution,'FAILED')

    def test_real_false_outcome(self):
        original = self.originals(bad=True)
        self.record = changed(self.record,reported_outcome='COMPLETED')
        self.assertEqual(self.invoke(originals=original)[1].eligibility_status,'REJECTED')

    def test_real_wrong_task(self):
        original = self.originals()
        self.record = changed(self.record,task_id='missing')
        with self.assertRaises(ValueError):
            self.invoke(originals=original)

    def test_real_wrong_agent(self):
        original = self.originals()
        self.record = changed(self.record,agent_id='other')
        with self.assertRaises(ValueError):
            self.invoke(originals=original)

    def test_real_workflow(self):
        original = self.originals()
        self.record = changed(self.record,workflow_id='other')
        with self.assertRaises(ValueError):
            self.invoke(originals=original)

    def test_real_planning_feedback_recovery(self):
        args = rf.fixture()
        result = rf.r.coordinate(*args)
        self.assertEqual(result[2].execution_status,'COORDINATION_RECORDED')
        self.assertEqual(args[0][4][0].consumed_budget,3)

    def test_real_qualification_blocker(self):
        fixture = qf.QualificationTests()
        fixture.setUp()
        self.assertIn('A09-001',fixture.run_assessment()[2].blocking_findings)

    def test_candidate_requires_independent_validation(self):
        with self.assertRaises(ValueError):
            l.make(l.LearningCandidate,candidate_id='candidate',supporting_experience_ids=('experience',),
                   proposed_learning_objective='DIAGNOSTIC_REVIEW_ONLY',required_validation=())

    def test_duplicate_policy_classes(self):
        with self.assertRaises(ValueError):
            changed(self.policy,allowed_evidence_classes=('REPORTED_ONLY','REPORTED_ONLY'))


if __name__ == '__main__':
    unittest.main()
