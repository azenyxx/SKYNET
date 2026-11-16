from .evidence import commitment,need
DOMAINS=(
('CAP-001','Logical consistency','Engine.submit/evaluate','Conflicting explicit verdicts only; no propositional theorem prover.','RULE_BASED'),
('CAP-002','Multi-step reasoning','System.run','Host supplies fixed completion/persistence/verification pipeline; no constructed reasoning.','FIXED_PIPELINE'),
('CAP-003','Goal decomposition',None,'No goal-to-subtask generation interface in inspected source.','UNAVAILABLE'),
('CAP-004','Planning','Scheduler.admit/dispatch/complete','Externally supplied dependency graphs and resource allocation; no autonomous plan construction.','SCHEDULING'),
('CAP-005','Memory utilization','Store.transact/read','Exact committed retrieval and stale CAS; no knowledge transfer or contextual reasoning.','STORAGE'),
('CAP-006','Knowledge transfer',None,'No learning/transfer execution interface or measured no-transfer experiment.','UNAVAILABLE'),
('CAP-007','Adaptive problem solving','RecoveryExecutor.execute','Explicit host-selected RETRY/RELEASE_LEASE rules; no novel response selection.','PROGRAMMED_RECOVERY'),
('CAP-008','Uncertainty handling','Engine.evaluate','Fixed thresholds and conflict abstention; no probabilistic uncertainty estimation.','RULE_BASED'),
('CAP-009','Self-correction',None,'Verifier rejects contradictions but no interface diagnoses and repairs erroneous reasoning.','UNAVAILABLE'),
('CAP-010','Cross-domain generalization',None,'No general-purpose reasoning interface or held-out learned model.','UNAVAILABLE'))
def registry(results=()):
 out=[]
 for cid,name,interface,limit,kind in DOMAINS:
  rows=[x for x in results if x['task']['domain']==cid];passed=sum(x['execution_status']=='PASS' for x in rows)
  status='UNAVAILABLE' if interface is None else ('PARTIALLY_DEMONSTRATED' if passed else 'NOT_DEMONSTRATED')
  out.append(dict(capability_id=cid,description=name,relevant_modules={'CAP-001':['skynet_sys_verification'],'CAP-002':['skynet','skynet_sys_workers','skynet_sys_memory','skynet_sys_transport'],'CAP-004':['skynet_sys_scheduler'],'CAP-005':['skynet_sys_memory'],'CAP-007':['skynet_sys_recovery','skynet.coordination'],'CAP-008':['skynet_sys_verification']}.get(cid,[]),execution_interface=interface,required_inputs='Bounded benchmark input DTO',expected_outputs='Observed public API states; independently scored',evidence_requirements='Actual calls, commitments, raw output and source binding',limitations=[limit,'Local structural commitments do not establish independent authenticity.'],qualification_status=status,observed_passes=passed,measurement_kind=kind))
 return out
