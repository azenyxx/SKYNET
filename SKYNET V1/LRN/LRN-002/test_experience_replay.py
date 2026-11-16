import unittest
from dataclasses import fields, replace, FrozenInstanceError
from unittest.mock import patch
import experience_replay as r
import test_learning_foundation as lf


def changed(obj, **changes):
    values={f.name:getattr(obj,f.name) for f in fields(obj) if f.name!='commitment'}
    values.update(changes)
    return r.make(type(obj),**values)


def source(name='one', real=False, bad=False, trust=None, provenance=None, outcome=None):
    f=lf.LearningTests();f.setUp()
    originals=f.originals(bad=bad) if real else ()
    f.record=lf.changed(f.record,experience_id=name)
    updates={'experience_id':name,'evidence_id':'e:'+name}
    if trust is not None:updates['verification_level']=trust
    if provenance is not None:updates['provenance_ref']=provenance
    if outcome is not None:f.record=lf.changed(f.record,reported_outcome=outcome)
    f.evidence=lf.changed(f.evidence,**updates)
    assessment=f.invoke(originals=None if originals==() else originals)[1]
    inputs=(f.policy,f.state,originals)
    pin=r.digest((f.record,f.evidence,assessment,inputs))
    return r.make(r.ReplaySource,source_id=name,record=f.record,evidence=f.evidence,
                  assessment=assessment,verification_inputs=inputs,source_commitment=pin)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.sources=(source(),)
        self.policy=r.make(r.SelectionPolicy,policy_id='policy',accepted_trust_classes=('REPORTED_ONLY','PARTIALLY_VERIFIED'),
                           ordering_strategy='CANONICAL_ID',max_batch=8,per_source=8,per_task=8,per_goal=8,max_operations=32,resource_ceiling=64)
        self.state=r.initial(self.policy)
        self.request_id='request'

    def invoke(self, **overrides):
        request=r.make(r.SelectionRequest,request_id=self.request_id,source_set_commitment=r.source_set(self.sources),
                       requested_scope=tuple(s.source_id for s in self.sources),policy_commitment=self.policy.commitment,
                       host_authorization_ref='host',sequence=len(self.state.processed_request_ids)+1)
        options=dict(expected_state=self.state.commitment,approved_request=request.commitment,expected_policy=self.policy.commitment)
        options.update(overrides)
        return r.replay(self.sources,request,self.policy,self.state,**options)

    def test_reported_diagnostic(self):
        self.assertEqual(self.invoke()[3][0].verification_status,'REPORTED_ONLY')

    def test_partial_preserved(self):
        self.sources=(source(real=True),)
        self.assertEqual(self.invoke()[3][0].verification_status,'PARTIALLY_VERIFIED')

    def test_failed_outcome(self):
        self.sources=(source(real=True,bad=True),)
        self.assertEqual(self.invoke()[3][0].observed_source_status,'FAILED')

    def test_missing_provenance(self):
        self.sources=(source(provenance=''),)
        self.assertEqual(self.invoke()[1].exclusion_reasons,('MISSING_PROVENANCE',))

    def test_contradiction(self):
        self.sources=(source(trust='CONTRADICTED'),)
        self.assertEqual(self.invoke()[1].exclusion_reasons,('CONTRADICTED',))

    def test_potential_conflict(self):
        self.sources=(source(),source('two',outcome='FAILED'))
        self.assertEqual(self.invoke()[1].exclusion_reasons,('POTENTIAL_CONFLICT','POTENTIAL_CONFLICT'))

    def test_duplicate_evidence_excluded(self):
        self.sources=(source(),source('two'))
        self.assertEqual(self.invoke()[1].coverage[3],1)

    def test_empty(self):
        self.sources=()
        self.assertEqual(self.invoke()[-1].replay_status,'EMPTY')

    def test_duplicate_id_rejected(self):
        self.sources*=2
        with self.assertRaises(ValueError):
            self.invoke()

    def test_forged_source(self):
        with self.assertRaises(ValueError):
            changed(self.sources[0],source_commitment='0'*64)

    def test_forged_commitment(self):
        with self.assertRaises(ValueError):
            replace(self.policy,commitment='0'*64)

    def test_version(self):
        with self.assertRaises(ValueError):
            changed(self.policy,version='bad')

    def test_identifier(self):
        with self.assertRaises(ValueError):
            changed(self.policy,policy_id='../bad')

    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            self.policy.max_batch=10

    def test_order_invalid(self):
        with self.assertRaises(ValueError):
            changed(self.policy,ordering_strategy='RANDOM')

    def test_false_verified(self):
        with self.assertRaises(ValueError):
            changed(self.policy,accepted_trust_classes=('VERIFIED_LOCAL',))

    def test_unknown_trust(self):
        with self.assertRaises(ValueError):
            changed(self.policy,accepted_trust_classes=('TRUST_ME',))

    def test_negative_quota(self):
        with self.assertRaises(ValueError):
            changed(self.policy,per_task=-1)

    def test_bool_quota(self):
        with self.assertRaises(ValueError):
            changed(self.policy,per_task=True)

    def test_inconsistent_quota(self):
        with self.assertRaises(ValueError):
            changed(self.policy,per_goal=9)

    def test_budget_accounting(self):
        state=self.invoke()[0]
        self.assertEqual((state.consumed,state.remaining),(2,62))

    def test_coverage_total(self):
        coverage=self.invoke()[1].coverage
        self.assertEqual(coverage[0],coverage[1]+coverage[2])

    def test_unresolved_count(self):
        self.sources=(source(provenance=''),)
        self.assertEqual(self.invoke()[1].coverage[4],1)

    def test_distribution(self):
        self.assertEqual(self.invoke()[1].coverage[5],(('REPORTED_ONLY',1),))

    def test_stale(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_state='0'*64)

    def test_request_replay(self):
        self.state=self.invoke()[0]
        with self.assertRaises(ValueError):
            self.invoke()

    def test_cross_call_dedup(self):
        self.state=self.invoke()[0];self.request_id='second'
        out=self.invoke()
        self.assertEqual(out[3],())
        self.assertEqual(out[0].replay_operations,1)

    def test_budget_escalation(self):
        self.state=changed(self.state,remaining=65)
        with self.assertRaises(ValueError):
            self.invoke()

    def test_host_authorization(self):
        with self.assertRaises(ValueError):
            self.invoke(approved_request='0'*64)

    def test_policy_pin(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_policy='0'*64)

    def test_stop(self):
        with self.assertRaises(ValueError):
            self.invoke(stop=True)

    def test_deadline(self):
        with self.assertRaises(ValueError):
            self.invoke(now=1,deadline=1)

    def test_atomic(self):
        old=self.state
        with self.assertRaises(ValueError):
            self.invoke(stop=True)
        self.assertEqual(old,self.state)

    def test_model_update(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],model_update_authorized=True)

    def test_knowledge(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],knowledge_promotion_authorized=True)

    def test_production(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],production_authorized=True)

    def test_learning(self):
        with self.assertRaises(ValueError):
            changed(self.invoke()[-1],learning_authorized=True)

    def test_determinism(self):
        self.assertEqual(self.invoke(),self.invoke())

    def test_canonical_tie(self):
        self.sources=(source('z'),source('a'))
        self.assertEqual(self.invoke()[2].ordered_experience_refs,('a',))

    def test_source_sequence(self):
        self.policy=changed(self.policy,ordering_strategy='SOURCE_SEQUENCE');self.state=r.initial(self.policy)
        self.sources=(source('z'),source('a'))
        self.assertEqual(self.invoke()[2].ordered_experience_refs,('a',))

    def test_priority(self):
        self.policy=changed(self.policy,ordering_strategy='VERIFICATION_PRIORITY');self.state=r.initial(self.policy)
        self.sources=(source('a'),source('z',real=True))
        self.assertEqual(self.invoke()[2].ordered_experience_refs,('z','a'))

    def test_input_order_irrelevant(self):
        sources=(source('z'),source('a'))
        self.assertEqual(r.source_set(sources),r.source_set(tuple(reversed(sources))))

    def test_real_eligibility_preserved(self):
        self.sources=(source(real=True),)
        self.assertEqual(self.invoke()[3][0].source_eligibility,'REQUIRES_VERIFICATION')

    def test_real_conflicting_result(self):
        self.sources=(source(real=True,bad=True,outcome='COMPLETED'),)
        self.assertEqual(self.invoke()[1].exclusion_reasons,('CONTRADICTED',))

    def test_real_no_task_dispatch(self):
        self.sources=(source(real=True),)
        with patch.object(lf.l.memory.gov,'govern',side_effect=AssertionError('dispatch')):
            self.assertEqual(len(self.invoke()[3]),1)


if __name__=='__main__':
    unittest.main()
