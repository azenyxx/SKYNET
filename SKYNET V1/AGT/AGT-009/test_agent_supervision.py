import unittest
from dataclasses import replace
import agent_supervision as s
import test_agent_recovery as fixtures


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.args = tuple(fixtures.fixture())
        result = s.recovery.coordinate(*self.args)
        src = self.args[0]
        workflow = s.make(s.WorkflowLifecycle, workflow_id='workflow', goal_id=src[0].goal_id,
                          plan_commitment=src[1].plan_commitment,
                          task_statuses=tuple((t.task_id, t.execution_status) for t in src[4][2][1].task_outcomes))
        agent = s.make(s.AgentLifecycle, agent_id='agent', status='RUNNING',
                       approved_capabilities=('READ_CONTEXT',), current_task='A')
        rs = result[0]
        self.state = s.make(s.SupervisionState, active_workflow=workflow, agent=agent,
                            processed_requests=(), confirmed_consumption=rs.consumed_budget,
                            uncertain_consumption=rs.uncertain_consumption,
                            reserved_capacity=rs.reserved_capacity, remaining_budget=rs.remaining_budget, history=())
        self.policy = s.make(s.SupervisionPolicy, policy_id='policy', allowed_transitions=s.TRANSITIONS,
                             resource_ceiling=10, stop_rules='REJECT_ALL')
        self.request = s.make(s.TransitionRequest, request_id='record', source_status='RUNNING',
                              target_status='FAILED', actor_id='agent', reason='OBSERVED',
                              source_state_commitment=self.state.state_commitment)
        self.auth = s.make(s.TransitionAuthorization, authorization_id='host',
                           request_commitment=self.request.request_commitment,
                           approved_transition=('RUNNING', 'FAILED'), authorized_actor='agent')
        self.kw = dict(expected_state=self.state.state_commitment, expected_source=s.digest(self.args),
                       approved_authorizations=(self.auth.authorization_commitment,),
                       expected_policy=self.policy.policy_commitment, observation_sequence=1)

    def invoke(self, **changes):
        return s.supervise(self.args, self.state, self.request, self.auth, self.policy, **(self.kw | changes))

    def test_real_chain_terminal_record(self):
        state, verdict = self.invoke()
        self.assertEqual(state.agent.status, 'FAILED')
        self.assertEqual(verdict.transition_status, 'ALLOW_RECORD')

    def test_stop(self):
        with self.assertRaises(ValueError):
            self.invoke(stop=True)

    def test_deadline(self):
        with self.assertRaises(ValueError):
            self.invoke(now=1, deadline=1)

    def test_stale_state(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_state='0' * 64)

    def test_unauthorized(self):
        with self.assertRaises(ValueError):
            self.invoke(approved_authorizations=())

    def test_wrong_source(self):
        with self.assertRaises(ValueError):
            self.invoke(expected_source='0' * 64)

    def test_out_of_order(self):
        with self.assertRaises(ValueError):
            self.invoke(observation_sequence=2)

    def test_determinism(self):
        self.assertEqual(self.invoke(), self.invoke())

    def test_atomic_rejection(self):
        before = s.digest(self.state)
        with self.assertRaises(ValueError):
            self.invoke(stop=True)
        self.assertEqual(before, s.digest(self.state))

    def test_conservation(self):
        state = self.invoke()[0]
        self.assertEqual(state.confirmed_consumption + state.uncertain_consumption +
                         state.reserved_capacity + state.remaining_budget, 10)

    def test_no_production(self):
        self.assertFalse(self.invoke()[1].production_authorized)

    def test_no_promotion(self):
        self.assertFalse(self.invoke()[1].knowledge_promotion_authorized)

    def test_forged_commitment(self):
        with self.assertRaises(ValueError):
            replace(self.state, state_commitment='0' * 64)

    def test_version(self):
        with self.assertRaises(ValueError):
            replace(self.request, schema_version='unknown')

    def test_false_authority(self):
        with self.assertRaises(ValueError):
            s.make(s.SupervisionVerdict, transition_status='ALLOW_RECORD', reason_code='test',
                   verification_status='VERIFIED', production_authorized=True)


if __name__ == '__main__':
    unittest.main()
