import unittest,time,json
from dataclasses import replace
from skynet_sys_verification import *
from skynet_sys.errors import ContractError
T='2026-10-25T00:00:00.000000Z'
def payload():return FrozenJSON.make({'answer':1})
def req(k='r',policy='single',**kw):return VerificationRequest(k,'task:'+k,digest('worker-result-v1',payload()),'producer',('STRUCTURE','EVIDENCE'),policy,0,**kw)
def engine():return Engine(HostPolicy('host',(('producer','cognitive.reason'),)+tuple(('v'+str(i),'cognitive.verify') for i in range(10))),(Policy('single','SINGLE_AUTHORIZED',('v0',)),Policy('quorum','QUORUM',('v0','v1','v2'),2),Policy('all','UNANIMOUS',('v0','v1','v2'),1)))
def assessment(q,v='v0',verdict='PASS',aid=None):
 e=EvidenceReference('e:'+q.request_id+':'+v,v,q.task_id,q.result_commitment,'result',T,'UNVERIFIED');return VerificationAssessment(aid or 'a:'+q.request_id+':'+v,q.request_id,v,verdict,(e,),('STRUCTURAL_ONLY',),0)
class Tests(unittest.TestCase):
 def bad(self,code,f):
  with self.assertRaisesRegex(VerificationError,'^'+code+'$'):f()
 def run_case(self,case):
  e=engine();q=req(policy='quorum');e.open(q,payload());a=assessment(q)
  if case=='schema':self.bad('SCHEMA',lambda:replace(q,schema_version='bad'))
  elif case=='identity':
   with self.assertRaisesRegex(ContractError,'^INVALID_IDENTITY$'):replace(q,request_id='../x')
  elif case=='digest':
   with self.assertRaisesRegex(ContractError,'^INVALID_DIGEST$'):replace(q,result_commitment='bad')
  elif case=='checks':self.bad('CHECKS',lambda:replace(q,required_checks=('STRUCTURE',)))
  elif case=='tick':self.bad('NUMBER',lambda:replace(q,logical_tick=True))
  elif case=='verdict':self.bad('VERDICT',lambda:replace(a,verdict='VERIFIED'))
  elif case=='reason':self.bad('REASONS',lambda:replace(a,reason_codes=()))
  elif case=='frozen':
   with self.assertRaises(AttributeError):q.task_id='new'
  elif case=='producer':self.bad('UNAUTHORIZED',lambda:engine().open(replace(q,producer_id='evil'),payload()))
  elif case=='verifier':self.bad('VERIFIER',lambda:e.submit(replace(a,verifier_id='evil'),0))
  elif case=='authority':e.authority=HostPolicy('no');self.bad('UNAUTHORIZED',lambda:e.submit(a,0))
  elif case=='empty_evidence':self.bad('EVIDENCE',lambda:replace(a,evidence_refs=()))
  elif case=='wrong_subject':self.bad('EVIDENCE_BINDING',lambda:e.submit(replace(a,evidence_refs=(replace(a.evidence_refs[0],subject_id='wrong'),)),0))
  elif case=='wrong_artifact':self.bad('EVIDENCE_BINDING',lambda:e.submit(replace(a,evidence_refs=(replace(a.evidence_refs[0],artifact_digest='f'*64),)),0))
  elif case=='evidence_producer':self.bad('EVIDENCE_PRODUCER',lambda:e.submit(replace(a,evidence_refs=(replace(a.evidence_refs[0],producer_id='v1'),)),0))
  elif case=='rejected_evidence':self.bad('EVIDENCE_STATUS',lambda:e.submit(replace(a,evidence_refs=(replace(a.evidence_refs[0],verification_status='REJECTED'),)),0))
  elif case=='unverified':e.submit(a,0);self.assertEqual(e.rounds['r']['assessments'][0].evidence_refs[0].verification_status,'UNVERIFIED')
  elif case=='bad_payload':self.bad('RESULT_COMMITMENT',lambda:engine().open(q,FrozenJSON.make({})))
  elif case.startswith('policy_'):
   kind,count,verdict=case[7:].split(':');ee=engine();qq=req(policy=kind);ee.open(qq,payload())
   for i in range(int(count)):ee.submit(assessment(qq,'v'+str(i),verdict),0)
   expected=verdict if int(count)>={'single':1,'quorum':2,'all':3}[kind] else 'INCONCLUSIVE';self.assertEqual(ee.evaluate('r',0).final_verdict,expected)
  elif case=='opposite':e.submit(a,0);e.submit(assessment(q,'v1','FAIL'),0);self.assertEqual(e.evaluate('r',0).final_verdict,'INCONCLUSIVE')
  elif case=='duplicate':e.submit(a,0);self.bad('DUPLICATE_ASSESSMENT',lambda:e.submit(a,0))
  elif case=='changed_duplicate':e.submit(a,0);e.submit(replace(a,verdict='FAIL'),0);self.assertTrue(e.rounds['r']['conflicts'])
  elif case=='identity_reuse':e.submit(a,0);e.submit(replace(a,assessment_id='new'),0);self.assertEqual(len(e.rounds['r']['assessments']),1)
  elif case=='revision':e.submit(a,0);e.submit(replace(a,revision=2),0);self.assertEqual(e.evaluate('r',0).final_verdict,'INCONCLUSIVE')
  elif case=='stale':self.bad('STALE_ASSESSMENT',lambda:e.submit(a,11))
  elif case=='stale_evidence':self.bad('STALE_EVIDENCE',lambda:e.submit(replace(a,evidence_refs=(replace(a.evidence_refs[0],created_at='2026-10-24T00:00:00.000000Z'),)),0))
  elif case=='terminal_conflict':e.evaluate('r',0);self.bad('TERMINAL',lambda:e.submit(a,0))
  elif case=='task_result':
   e.evaluate('r',0);new=replace(q,request_id='new',previous_round='r',result_commitment=digest('worker-result-v1',FrozenJSON.make({})));e.open(new,FrozenJSON.make({}));self.assertTrue(e.rounds['new']['conflicts'])
  elif case=='conflict_stable':e.submit(a,0);e.submit(replace(a,verdict='FAIL'),0);self.assertEqual(e.rounds['r']['conflicts'],e.replay(e.journal).rounds['r']['conflicts'])
  elif case=='open':self.assertEqual(e.rounds['r']['status'],'OPEN')
  elif case=='collect':e.submit(a,0);self.assertEqual(e.rounds['r']['status'],'COLLECTING')
  elif case=='evaluate_trace':e.evaluate('r',0);self.assertIn('EVALUATING',e.rounds['r']['trace'])
  elif case=='terminal':e.evaluate('r',0);self.bad('TERMINAL',lambda:e.evaluate('r',0))
  elif case=='linked':e.evaluate('r',0);e.open(replace(q,request_id='new',previous_round='r'),payload());self.assertEqual(e.rounds['new']['status'],'OPEN')
  elif case=='bad_link':self.bad('PREVIOUS_ROUND',lambda:e.open(replace(q,request_id='new',previous_round='missing'),payload()))
  elif case=='replay':e.submit(a,0);e.evaluate('r',0);self.assertEqual(e.state_digest(),e.replay(e.journal).state_digest())
  elif case=='tamper':self.bad('JOURNAL_TAMPERED',lambda:e.replay((replace(e.journal[0],entry_hash='f'*64),)))
  elif case=='reorder':e.submit(a,0);self.bad('JOURNAL_CHAIN',lambda:e.replay(e.journal[::-1]))
  elif case=='duplicate_journal':self.bad('JOURNAL_CHAIN',lambda:e.replay(e.journal+e.journal))
  elif case=='mismatch':
   entry=replace(e.journal[0],state_digest='f'*64);entry=replace(entry,entry_hash=digest('verification-journal-v1',entry.body()));self.bad('REPLAY_MISMATCH',lambda:e.replay((entry,)))
  elif case=='determinism':other=engine();other.open(q,payload());self.assertEqual(e.journal,other.journal)
  else:raise AssertionError(case)
cases=['schema','identity','digest','checks','tick','verdict','reason','frozen','producer','verifier','authority','empty_evidence','wrong_subject','wrong_artifact','evidence_producer','rejected_evidence','unverified','bad_payload']
cases += ['policy_'+k+':'+str(n)+':'+v for k,n,v in [('single',0,'PASS'),('single',1,'PASS'),('single',1,'FAIL'),('single',1,'REJECTED'),('quorum',0,'PASS'),('quorum',1,'PASS'),('quorum',2,'PASS'),('quorum',2,'FAIL'),('all',1,'PASS'),('all',2,'PASS'),('all',3,'PASS'),('all',3,'FAIL')]]
cases += ['opposite','duplicate','changed_duplicate','identity_reuse','revision','stale','stale_evidence','terminal_conflict','task_result','conflict_stable','open','collect','evaluate_trace','terminal','linked','bad_link','replay','tamper','reorder','duplicate_journal','mismatch','determinism']
for name in cases:
 def test(self,name=name):self.run_case(name)
 setattr(Tests,'test_'+name.replace(':','_'),test)
class Load(unittest.TestCase):
 def test_100_requests(self):
  t=time.monotonic();e=engine();counts={};assessments=0
  for i in range(100):
   kind=('single','quorum','all')[i%3];q=req('r'+str(i),kind);e.open(q,payload());n={'single':1,'quorum':2,'all':3}[kind]
   for j in range(n):e.submit(assessment(q,'v'+str(j),'FAIL' if i%5==0 else 'PASS'),0);assessments+=1
   if i<20:e.submit(replace(assessment(q),verdict='FAIL',revision=2,assessment_id='conflict:'+str(i)),0);assessments+=1
   d=e.evaluate(q.request_id,0);counts[d.final_verdict]=counts.get(d.final_verdict,0)+1
  conflicts=sum(len(r['conflicts']) for r in e.rounds.values());other=e.replay(e.journal);self.assertEqual(e.state_digest(),other.state_digest());self.assertGreaterEqual(conflicts,20);print('LOAD '+json.dumps({'requests':100,'configured_verifiers':10,'participating_verifiers':3,'assessments':assessments,'conflicts':conflicts,'verdicts':counts,'digest':e.state_digest(),'replay_digest':other.state_digest(),'seconds':time.monotonic()-t}))

from skynet_sys_verification.integration import IntegratedVerification
from test_workers import integrated
from skynet_sys_memory import Operation,MemoryError
from skynet_sys_transport.contracts import BusError
class IntegrationTests(unittest.TestCase):
 def fixture(self):
  workers=integrated();l=workers.dispatch('task','d',1,0);workers.complete('w',l.lease_id,1,'d',payload(),0);e=engine();e=Engine(HostPolicy('integration',(('w','cognitive.reason'),('v0','cognitive.verify'))),e.policies);q=replace(req(),task_id='task',producer_id='w');return IntegratedVerification(e,workers),q,l
 def test_completed_binding(self):i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);self.assertEqual(i.engine.rounds['r']['status'],'OPEN')
 def test_producer_binding(self):
  i,q,l=self.fixture()
  with self.assertRaisesRegex(VerificationError,'^RESULT_BINDING$'):i.run('open',(replace(q,producer_id='other'),payload()),l.lease_id)
 def test_result_binding(self):
  i,q,l=self.fixture()
  with self.assertRaisesRegex(VerificationError,'^RESULT_COMMITMENT$'):i.run('open',(q,FrozenJSON.make({})),l.lease_id)
 def test_missing_lease(self):
  i,q,l=self.fixture()
  with self.assertRaisesRegex(VerificationError,'^LEASE_BINDING$'):i.run('open',(q,payload()),'unknown')
 def test_memory_cas(self):
  i,q,l=self.fixture();i.workers.memory.transact('admin','external',(Operation('agent','verify:0','CREATE',0,FrozenJSON.make({})),),0);before=i.engine.state_digest()
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):i.run('open',(q,payload()),l.lease_id)
  self.assertEqual(before,i.engine.state_digest())
 def test_transport_pressure(self):
  i,q,l=self.fixture();i.workers.bus.config=replace(i.workers.bus.config,queue_limit=1);before=i.engine.state_digest()
  with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):i.run('open',(q,payload()),l.lease_id)
  self.assertEqual(before,i.engine.state_digest())
 def test_decision_storage(self):
  i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);i.run('submit',(assessment(q),0));d=i.run('evaluate',('r',0));self.assertEqual(d.final_verdict,'PASS');record=i.workers.memory.read('admin','agent','verify:2');self.assertEqual(record.evidence_refs[0].verification_status,'UNVERIFIED')
 def test_real_replay(self):i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);i.run('submit',(assessment(q),0));i.run('evaluate',('r',0));self.assertEqual(i.engine.state_digest(),i.engine.replay(i.engine.journal).state_digest())

class ClosureTests(IntegrationTests):
 # Inherited tests rerun real integration; additional distinct scenarios below.
 def test_ten_participants(self):
  e=engine();e.policies=(Policy('ten','UNANIMOUS',tuple('v'+str(i) for i in range(10))),);e=Engine(e.authority,e.policies);q=req(policy='ten');e.open(q,payload())
  for n in range(10):e.submit(assessment(q,'v'+str(n)),0)
  self.assertEqual(len({a.verifier_id for a in e.rounds['r']['assessments']}),10);self.assertEqual(e.evaluate('r',0).final_verdict,'PASS')
 def test_duplicate_audit(self):
  e=engine();q=req();e.open(q,payload());a=assessment(q);e.submit(a,0)
  with self.assertRaisesRegex(VerificationError,'^DUPLICATE_ASSESSMENT$'):e.submit(a,0)
  self.assertEqual(e.audit_records('r')[-1][2],'DUPLICATE_ASSESSMENT');self.assertEqual(len(e.rounds['r']['assessments']),1)
 def test_rejected_decision(self):
  e=engine();q=req();e.open(q,payload())
  with self.assertRaisesRegex(VerificationError,'^VERIFIER$'):e.submit(assessment(q,'v9'),0)
  d=e.evaluate('r',0);self.assertEqual(len(d.rejected_assessments),1);self.assertEqual(d.final_verdict,'INCONCLUSIVE')
 def test_conflict_details(self):
  e=engine();q=req();e.open(q,payload());a=assessment(q);e.submit(a,0);e.submit(replace(a,verdict='FAIL'),0)
  rows=e.audit_records('r');self.assertEqual(rows[1][0],'CONFLICT');self.assertEqual(rows[1][2],'ASSESSMENT_REVISION_CONFLICT');self.assertIn(rows[1][1],e.evaluate('r',0).conflict_refs)
 def test_rejection_replay(self):
  e=engine();q=req();e.open(q,payload())
  with self.assertRaisesRegex(VerificationError,'^VERIFIER$'):e.submit(assessment(q,'v9'),0)
  self.assertEqual(e.state_digest(),e.replay(e.journal).state_digest())
 def test_integrated_rejection_storage(self):
  i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id)
  with self.assertRaisesRegex(VerificationError,'^VERIFIER$'):i.run('submit',(assessment(q,'v9'),0))
  self.assertEqual(i.workers.memory.read('admin','agent','verify:1').payload.value()['audit_records'][0][0],'REJECTED');self.assertEqual(i.state_digest(),i.replay().state_digest())
 def test_composite_replay(self):
  i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);i.run('submit',(assessment(q),0));i.run('evaluate',('r',0));self.assertEqual(i.state_digest(),i.replay().state_digest());self.assertEqual(i.workers.state_digest(),i.replay().workers.state_digest())
 def test_composite_tamper(self):
  i,q,l=self.fixture();i.run('open',(q,payload()),l.lease_id);c=i.commands[0]
  with self.assertRaisesRegex(VerificationError,'^INTEGRATED_REPLAY_MISMATCH$'):i.replay((c[:4]+('f'*64,c[5]),))
 def test_terminal_audit_immutable(self):
  e=engine();q=req();e.open(q,payload());e.evaluate('r',0);before=e.state_digest()
  with self.assertRaisesRegex(VerificationError,'^TERMINAL$'):e.submit(assessment(q),0)
  self.assertEqual(before,e.state_digest())
 def test_evidence_not_promoted(self):
  e=engine();q=req();e.open(q,payload());a=assessment(q);e.submit(a,0);self.assertEqual(e.audit_records('r')[0][4],(a.evidence_refs[0].commitment,));self.assertEqual(a.evidence_refs[0].verification_status,'UNVERIFIED')
 def test_ten_verifier_load(self):
  start=time.monotonic();base=engine();policies=tuple(Policy('s'+str(i),'SINGLE_AUTHORIZED',('v'+str(i),)) for i in range(10))+(Policy('q','QUORUM',tuple('v'+str(i) for i in range(10)),2),Policy('u','UNANIMOUS',tuple('v'+str(i) for i in range(10))))
  e=Engine(base.authority,policies);participants=set();counts={};n=0
  for k in range(100):
   policy=('s'+str(k%10),'q','u')[k%3];q=req('load'+str(k),policy);e.open(q,payload());vs=[k%10] if k%3==0 else ([(k+j)%10 for j in range(2)] if k%3==1 else list(range(10)))
   for j in vs:e.submit(assessment(q,'v'+str(j),'FAIL' if k%5==0 else 'PASS'),0);participants.add('v'+str(j));n+=1
   if k<20:e.submit(replace(assessment(q,'v'+str(vs[0])),revision=2,verdict='FAIL'),0);n+=1
   d=e.evaluate(q.request_id,0);counts[d.final_verdict]=counts.get(d.final_verdict,0)+1
  other=e.replay(e.journal);self.assertEqual(e.state_digest(),other.state_digest());self.assertEqual(len(participants),10);self.assertEqual(set(counts),{'PASS','FAIL','INCONCLUSIVE'})
  print('CLOSURE_LOAD '+json.dumps({'requests':100,'participants':sorted(participants),'assessments':n,'conflicts':sum(len(r['conflicts']) for r in e.rounds.values()),'verdicts':counts,'digest':e.state_digest(),'replay_digest':other.state_digest(),'seconds':time.monotonic()-start}))
