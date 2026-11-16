import unittest
from dataclasses import replace, fields, FrozenInstanceError
import adaptive_learning as a
import test_experience_replay as fixtures


def changed(obj, **changes):
    values = {f.name:getattr(obj,f.name) for f in fields(obj) if f.name!='commitment'}
    values.update(changes)
    return a.make(type(obj), **values)


class Tests(unittest.TestCase):
    def setUp(self):
        f = fixtures.ReplayTests(); f.setUp()
        self.sources = f.sources
        self.rp, self.rs = f.policy, f.state
        self.policy = a.make(a.StrategyPolicy,policy_id='local',categories=a.CATEGORIES,resource_ceiling=8,max_estimated_cost=8)
        self.state = a.initial(self.policy)
        self.candidates = (a.make(a.StrategyCandidate,strategy_id='strategy',category='EVIDENCE_FILTERING',estimated_cost=1,uncertainty='NOT_ESTABLISHED'),)

    def invoke(self, **changes):
        req = a.replay.make(a.replay.SelectionRequest,request_id='request',source_set_commitment=a.replay.source_set(self.sources),
            requested_scope=tuple(s.source_id for s in self.sources),policy_commitment=self.rp.commitment,host_authorization_ref='host',sequence=1)
        args = (self.sources,req,self.rp,self.rs)
        pins = (self.rs.commitment,req.commitment,self.rp.commitment)
        options = dict(expected_state=self.state.commitment,approved_input=a.digest((self.candidates,args,pins,self.policy.commitment)),sequence=self.state.sequence+1)
        options.update(changes)
        return a.evaluate(self.candidates,args,pins,self.policy,self.state,**options)

    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.policy.resource_ceiling=2

    def test_commitment(self):
        with self.assertRaises(ValueError):
            replace(self.policy,commitment='0'*64)

    def test_version(self):
        with self.assertRaises(ValueError):
            changed(self.policy,version='bad')

    def test_category(self):
        with self.assertRaises(ValueError):
            changed(self.candidates[0],category='TRAIN')

    def test_boolean_cost(self):
        with self.assertRaises(ValueError):
            changed(self.candidates[0],estimated_cost=True)

    def test_reported_not_promoted(self):
        self.assertEqual(self.invoke()[1].classifications,('REPORTED_ONLY',))

    def test_filtering(self):
        self.assertEqual(self.invoke()[2][0].status,'REQUIRES_MORE_EVIDENCE')

    def test_reweighting(self):
        self.candidates=(changed(self.candidates[0],category='REPLAY_REWEIGHTING'),)
        self.assertEqual(self.invoke()[2][0].status,'REQUIRES_MORE_EVIDENCE')

    def test_scheduling(self):
        self.candidates=(changed(self.candidates[0],category='EVALUATION_SCHEDULING'),)
        self.assertEqual(self.invoke()[2][0].status,'REQUIRES_MORE_EVIDENCE')

    def test_cost_rejection(self):
        self.candidates=(changed(self.candidates[0],estimated_cost=9),)
        self.assertEqual(self.invoke()[2][0].status,'REJECTED')

    def test_comparison(self):
        self.candidates+=(changed(self.candidates[0],strategy_id='cheap',estimated_cost=1),)
        self.assertEqual(self.invoke()[3].ordered_strategy_ids,('cheap','strategy'))

    def test_proposal_advisory(self):
        self.assertEqual(self.invoke()[4][0].required_validation,('INDEPENDENT_EVIDENCE','SEPARATE_AUTHORIZATION'))

    def test_no_gain_claim(self):
        self.assertEqual(self.invoke()[3].basis,'ESTIMATED_COST_THEN_ID_NO_GAIN_CLAIM')

    def test_blockers(self):
        self.assertIn('A09-001',self.invoke()[4][0].blocking_findings)

    def test_empty_blocked(self):
        self.sources=()
        self.assertEqual(self.invoke()[2][0].status,'BLOCKED')

    def test_stale(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_state='0'*64)

    def test_budget(self):
        self.state=changed(self.state,remaining=9)
        with self.assertRaises(ValueError):
            self.invoke()

    def test_duplicate(self):
        self.state=self.invoke()[0]
        with self.assertRaises(ValueError):
            self.invoke()

    def test_sequence(self):
        with self.assertRaises(ValueError):
            self.invoke(sequence=2)

    def test_conservation(self):
        state=self.invoke()[0]
        self.assertEqual(state.consumed+state.remaining,8)

    def test_stop(self):
        with self.assertRaises(ValueError):
            self.invoke(stop=True)

    def test_deadline(self):
        with self.assertRaises(ValueError):
            self.invoke(now=1,deadline=1)

    def test_model_update(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],model_update_authorized=True)

    def test_production(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],production_authorized=True)

    def test_no_learning_or_promotion(self):
        verdict=self.invoke()[-1]
        self.assertFalse(verdict.learning_authorized or verdict.knowledge_promotion_authorized)

    def test_real_partial(self):
        self.sources=(fixtures.source(real=True),)
        self.assertEqual(self.invoke()[1].classifications,('PARTIALLY_VERIFIED',))

    def test_real_failed(self):
        self.sources=(fixtures.source(real=True,bad=True),)
        self.assertEqual(self.invoke()[1].outcomes,('FAILED',))

    def test_real_duplicate_selection(self):
        self.sources=(fixtures.source('a'),fixtures.source('b'))
        self.assertEqual(len(self.invoke()[1].classifications),1)

    def test_real_missing_provenance(self):
        self.sources=(fixtures.source(provenance=''),)
        self.assertEqual(self.invoke()[2][0].status,'BLOCKED')

    def test_real_determinism(self):
        self.sources=(fixtures.source(real=True),)
        self.assertEqual(self.invoke(),self.invoke())


if __name__=='__main__':
    unittest.main()
