"""One bounded read-only replay. No production, persistence or adoption."""
from integrated_qualification_contracts import *
import rollback_safety_engine as predecessor

def policy():return make(QualificationPolicy,policy_version='v1',mandatory_capabilities=CAPS,evidence_requirements=('ORIGINAL_REPLAY',),integration_requirements=STAGES,finding_rules='PRESERVE_ALL_NONEXHAUSTIVE',authorization_constraints=tuple((f,False) for f in FLAGS),resource_limits=7,prohibited_operations=('EXECUTION','ADOPTION','TRAINING','DEPLOYMENT','ACTUAL_ROLLBACK'))
def initial():return make(QualificationState,state_version='v1',sequence=0,previous_state_commitment='0'*64,assessed_stages=(),assessed_capabilities=(),unresolved_findings=FINDINGS,cumulative_resource_usage=0,state_commitment=digest(('initial',FINDINGS)))
def qualify(records,call,expected_result,policy,previous,*,state_pin,input_pin,sequence,stop=False,now=0,deadline=1,artifact_blobs=()):
 check(policy,QualificationPolicy);check(previous,QualificationState)
 need(type(records) is tuple and len(records)==7,'STAGES')
 for r in records:check(r,StageQualificationRecord)
 ids=tuple(r.stage_id for r in records);need(len(set(ids))==7,'DUPLICATE');need(tuple(sorted(ids))==STAGES,'STAGES')
 need(type(artifact_blobs) is tuple and len(artifact_blobs)==7,'ARTIFACT_UNAVAILABLE')
 need(all(type(pair) is tuple and len(pair)==2 for pair in artifact_blobs),'ARTIFACT_FORMAT')
 need(len(set(k for k,b in artifact_blobs))==7,'DUPLICATE_ARTIFACT')
 verified={k:verify_archive(k,b) for k,b in artifact_blobs}
 for r in records:
  need(r.stage_id in verified,'ARTIFACT_UNAVAILABLE');need(r==verified[r.stage_id],'EVIDENCE_BINDING')
 need(state_pin==previous.commitment,'STATE_PIN');need(previous.sequence==0 and type(sequence) is int and sequence==1,'REPLAY')
 need(input_pin==digest((tuple(sorted(records,key=lambda r:r.stage_id)),call,expected_result,policy)),'INPUT_PIN')
 need(type(stop) is bool and type(now) is int and type(deadline) is int,'CONTROL');need(not stop,'STOPPED');need(now<deadline,'DEADLINE');need(policy.resource_limits-previous.cumulative_resource_usage>=7,'OPERATION_BUDGET')
 need(type(call) is tuple and len(call)==10,'SOURCE')
 actual=predecessor.validate(*call,expected_state=call[-1].state_commitment,approved_input=v.digest(call[:-1]),sequence=call[-1].sequence+1)
 need(actual==expected_result,'RESULT_BINDING')
 need(all(flag is False for _,flag in actual[2].authorization_flags),'AUTHORITY')
 need(actual[2].unresolved_findings==v.BLOCKERS,'FINDINGS')
 failed=any(r.observed_test_results[1] or r.observed_test_results[2] for r in records)
 status='SERIES_FAILED' if failed else 'SERIES_BLOCKED' if any(r.integration_class=='NOT_TESTED' for r in records) else 'SERIES_CLOSED_PARTIAL'
 caps=tuple((c,'BLOCKED' if c=='autonomous_rsi' else 'FIXTURE_BASED_ONLY') for c in CAPS)
 verdict=make(IntegratedQualificationVerdict,qualification_id='qualification',stage_results=tuple((r.stage_id,r.reported_status) for r in sorted(records,key=lambda r:r.stage_id)),integration_result='FIXTURE_BASED_ONLY',capability_results=caps,evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',safety_status='NO_AUTHORIZATION',unresolved_findings=FINDINGS,series_status=status,decision_reasons=('OPEN_FINDINGS','SYNTHETIC_FIXTURES','INVENTORY_NOT_EXHAUSTIVE'),authorization_flags=tuple((f,False) for f in FLAGS))
 state=make(QualificationState,state_version='v1',sequence=1,previous_state_commitment=previous.commitment,assessed_stages=STAGES,assessed_capabilities=CAPS,unresolved_findings=FINDINGS,cumulative_resource_usage=7,state_commitment=digest((previous.commitment,input_pin,verdict.commitment)))
 return state,verdict

# Trusted deployment pins are artifact identity, not independent source authenticity.
import hashlib,json,zipfile,re
from io import BytesIO
ARTIFACT_PINS = {'RSI-001': 'c9599a7130ca42effd3a703ffe934d8b21e5ee783d7befbfd9f7cb705e9a6086', 'RSI-002': '00ea445e0eac8cfaedca59c21ecafd66024ce6f802c369ac6d6f28014081a263', 'RSI-003': 'a7b62e076a4746dc30a1bc308587ceeac5562340ae3f2dc05d36c6883bac16f7', 'RSI-004': '9b1eb0569bc9ae54e9e94a851dc3e11dfb9599853428f784e97a15cdbe71be02', 'RSI-005': 'b2388478976841a9015abea18d1e5d043f6d6d9956f6a90700e02bf9e3b5379c', 'RSI-006': '5e7f9837767065105e323a954b2d87157d0c03577b4dd631dd007b12ee49d652', 'RSI-007': 'f85cdce45cc51030dcfe384f3ba0c92f754c58f86ec7a382ce1ae224e6bff5c6'}
ARTIFACT_FILES = {
 'RSI-001':('rsi_contracts.py','self_improvement_foundation.py','test_self_improvement_foundation.py'),
 'RSI-002':('self_assessment_contracts.py','bottleneck_discovery.py','test_bottleneck_discovery.py'),
 'RSI-003':('improvement_hypothesis_contracts.py','improvement_proposal_engine.py','test_improvement_proposal_engine.py'),
 'RSI-004':('experiment_contracts.py','sandboxed_experimentation.py','test_sandboxed_experimentation.py'),
 'RSI-005':('comparative_evaluation_contracts.py','regression_gate_engine.py','test_regression_gate_engine.py'),
 'RSI-006':('governance_contracts.py','improvement_selection_engine.py','test_improvement_selection_engine.py'),
 'RSI-007':('versioning_contracts.py','rollback_safety_engine.py','test_rollback_safety_engine.py')}
def verify_archive(stage,data):
 need(stage in ARTIFACT_PINS,'STAGE');need(type(data) is bytes and len(data)<=1048576,'ARCHIVE_SIZE')
 sha=lambda b:hashlib.sha256(b).hexdigest()
 try:
  with zipfile.ZipFile(BytesIO(data)) as z:
   names=z.namelist();expected=set(ARTIFACT_FILES[stage])|{'FINAL-REPORT.md','TEST-OUTPUT.txt','MANIFEST.json','SHA256SUMS'}
   need(len(names)==7 and set(names)==expected,'ARCHIVE_FILES');need(all(i.file_size<=1048576 and not i.is_dir() for i in z.infolist()),'ARCHIVE_SIZE');need(z.testzip() is None,'CRC')
   files={n:z.read(n) for n in names};manifest=json.loads(files['MANIFEST.json']);entries=manifest.get('files')
   need(type(entries) is list and len(entries)==5,'MANIFEST');need({r.get('path') for r in entries}==expected-{'MANIFEST.json','SHA256SUMS'},'MANIFEST')
   for r in entries:
    need(type(r.get('size')) is int and r['size']==len(files[r['path']]) and r.get('sha256')==sha(files[r['path']]),'MANIFEST')
   sums=files['SHA256SUMS'].decode().splitlines();need(len(sums)==6,'CHECKSUMS');seen=set()
   for line in sums:
    parts=line.split('  ',1);need(len(parts)==2,'CHECKSUMS');h,n=parts;need(n in files and n!='SHA256SUMS' and n not in seen and h==sha(files[n]),'CHECKSUMS');seen.add(n)
   need(seen==expected-{'SHA256SUMS'},'CHECKSUMS')
   need(sha(data)==ARTIFACT_PINS[stage],'ARTIFACT_HASH')
   log=files['TEST-OUTPUT.txt'].decode();m=re.findall(r'^Ran (\d+) tests? in ',log,re.M);need(len(m)==1,'TEST_LOG')
   counts=tuple(len(re.findall(pattern,log,re.M)) for pattern in (r' \.\.\. ok$',r' \.\.\. FAIL$',r' \.\.\. ERROR$',r' \.\.\. skipped.*$'))
   need(sum(counts)==int(m[0]),'TEST_COUNT')
   report=files['FINAL-REPORT.md'].decode();need('CLOSED PARTIAL' in report,'REPORTED_STATUS')
   return make(StageQualificationRecord,stage_id=stage,stage_version='R2' if stage=='RSI-007' else 'v1',artifact_commitment=sha(data),reported_status='CLOSED_PARTIAL',observed_test_results=counts,integration_class='FIXTURE_BASED_ONLY',evidence_refs=(sha(files['TEST-OUTPUT.txt']),sha(files['FINAL-REPORT.md'])),qualification_limitations=('ARTIFACT_INTEGRITY_VERIFIED','REPORTED_TEST_RESULTS','RUNTIME_NOT_INDEPENDENTLY_RERUN','NON_EXHAUSTIVE'))
 except (zipfile.BadZipFile,UnicodeError,json.JSONDecodeError,KeyError,TypeError):raise ValueError('ARCHIVE_FORMAT')
def register():
 return tuple(make(QualificationFinding,finding_id=f,severity='P1' if f in ('RSI07-004','RSI07-R1-001','RSI08-001','RSI08-002') else 'P2' if f=='RSI08-003' else 'UNKNOWN',originating_stage=f.split('-')[0],affected_capabilities=('qualification',),evidence_refs=('OWNER_SPECIFICATION',),current_status='OPEN',closure_requirements=('INDEPENDENT_EVIDENCE','ORIGINAL_DESCRIPTION_REQUIRED'),inherited_flag=True) for f in FINDINGS)
