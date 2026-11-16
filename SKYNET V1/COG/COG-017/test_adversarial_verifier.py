import unittest
from dataclasses import replace,FrozenInstanceError
from cognitive_adversarial_contracts import *
from cognitive_adversarial_verifier import verify

class Tests(unittest.TestCase):
    def setUp(self):
        self.e=EvidenceReference('e','x',7,'observer',(),0,100,False)
        self.t=VerificationTarget('t','producer','x',7,'DIRECT',('e',))
        self.r=VerificationRequest('r',self.t,('e',),'local-structural-v1',1000,10,20,False)
    def runv(self,r=None,es=None,pins=None):
        es=(self.e,) if es is None else es
        return verify(self.r if r is None else r,es,tuple((e.evidence_id,commitment(e)) for e in es) if pins is None else pins)
    def has(self,code,**kw):self.assertIn(code,{f.reason_code for f in self.runv(**kw).findings})
    def test_contract_bool(self):
        with self.assertRaises(ValueError):replace(self.r,max_checks=True)
    def test_contract_negative(self):
        with self.assertRaises(ValueError):replace(self.r,now=-1)
    def test_contract_unknown(self):
        with self.assertRaises(TypeError):VerificationTarget(**dict(asdict(self.t),authority=True))
    def test_contract_version(self):
        with self.assertRaises(ValueError):replace(self.r,schema_version='v2')
    def test_contract_identifier(self):
        with self.assertRaises(ValueError):replace(self.t,target_id='run shell!')
    def test_contradiction(self):self.has('CONCLUSION_CONTRADICTED',r=replace(self.r,target=replace(self.t,conclusion=8)))
    def test_bad_sum(self):self.has('INVALID_CONCLUSION',r=replace(self.r,target=replace(self.t,inference='SUM',conclusion=8)))
    def test_valid_sum(self):self.assertEqual(self.runv(r=replace(self.r,target=replace(self.t,inference='SUM'))).status,'INCONCLUSIVE')
    def test_unsupported(self):self.has('NO_SUPPORT',r=replace(self.r,target=replace(self.t,dependencies=())))
    def test_wrong_subject(self):self.has('INVALID_INFERENCE',r=replace(self.r,target=replace(self.t,subject='y')))
    def test_conflicting(self):
        e2=replace(self.e,evidence_id='f',value=8)
        self.has('CONFLICTING_EVIDENCE',r=replace(self.r,evidence_refs=('e','f')),es=(self.e,e2))
    def test_missing_reference(self):self.assertEqual(self.runv(es=()).status,'BLOCKED')
    def test_bad_pin(self):self.has('INTEGRITY_UNVERIFIED',pins=(('e','0'*64),))
    def test_missing_pin(self):self.has('INTEGRITY_UNVERIFIED',pins=())
    def test_missing_dependency(self):self.has('MISSING_DEPENDENCY',es=(replace(self.e,dependencies=('absent',)),))
    def test_cycle(self):self.has('CIRCULAR_OR_MISSING',es=(replace(self.e,dependencies=('e',)),))
    def test_expiry(self):self.has('STALE_OR_FUTURE',es=(replace(self.e,expires_at=9),))
    def test_self_evidence(self):self.has('SELF_EVIDENCE',es=(replace(self.e,source='producer'),))
    def test_no_independence(self):self.has('INDEPENDENCE_NOT_ESTABLISHED')
    def test_producer_verdict(self):self.assertEqual(verify({'status':'VERIFIED'},(),()).status,'BLOCKED')
    def test_no_promotion(self):self.assertFalse(self.runv().promotion_authorized)
    def test_no_production(self):self.assertFalse(self.runv().production_authorized)
    def test_refuted(self):self.assertEqual(self.runv(r=replace(self.r,target=replace(self.t,conclusion=8))).status,'REFUTED')
    def test_inconclusive(self):self.assertEqual(self.runv().status,'INCONCLUSIVE')
    def test_blocked(self):self.assertEqual(self.runv(pins=()).status,'BLOCKED')
    def test_refutation_not_bad_origin(self):self.assertEqual(self.runv(r=replace(self.r,target=replace(self.t,conclusion=8)),pins=()).status,'BLOCKED')
    def test_evidence_retained(self):self.assertEqual(self.runv().evidence_refs,('e',))
    def test_stop(self):self.has('STOPPED',r=replace(self.r,stop=True))
    def test_deadline(self):self.has('DEADLINE_EXHAUSTED',r=replace(self.r,deadline=10))
    def test_budget(self):self.has('RESOURCE_EXHAUSTED',r=replace(self.r,max_checks=1))
    def test_unknown_policy(self):self.assertEqual(self.runv(r=replace(self.r,policy_id='other')).status,'BLOCKED')
    def test_malformed_snapshot(self):self.assertEqual(verify(self.r,[],()).status,'BLOCKED')
    def test_replay(self):self.assertEqual(self.runv(),self.runv())
    def test_digest(self):self.assertEqual(self.runv().verdict_id,self.runv().verdict_id)
    def test_changed_input(self):self.assertNotEqual(self.runv().verdict_id,self.runv(r=replace(self.r,request_id='r2')).verdict_id)
    def test_immutable(self):
        before=commitment(self.r);self.runv();self.assertEqual(before,commitment(self.r))
        with self.assertRaises(FrozenInstanceError):self.e.value=9

if __name__=='__main__':unittest.main()
