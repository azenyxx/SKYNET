"""Offline qualification of the inspected COG017-019 surface only.
Records are local observations, not attestations. Historical debt is owner-supplied.
"""
from dataclasses import dataclass,fields,is_dataclass,replace
from fractions import Fraction as F
import hashlib,json,re
import cognitive_unified as u
ac,av,bm=u.ac,u.av,u.bm

def need(v,code='CONTRACT'):
    if not v:raise ValueError(code)
def ident(v):need(type(v) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,96}',v) is not None)
def plain(v):
    if type(v) is dict:
        need(all(type(k) is str for k in v), 'DICT_KEY_TYPE')
        return {k:plain(value) for k,value in v.items()}
    if is_dataclass(v):return {f.name:plain(getattr(v,f.name)) for f in fields(v)}
    if type(v) is tuple:return [plain(x) for x in v]
    if type(v) is F:return [v.numerator,v.denominator]
    return v
def canonical(v):return json.dumps(plain(v),sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(v):return hashlib.sha256(b'SKYNET:COG020:v1\0'+canonical(v).encode()).hexdigest()
def hexhash(v):need(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None)

@dataclass(frozen=True)
class QualificationCase:
    record_id:str
    source_component:str
    evidence_commitment:str
    execution_status:str
    reason_code:str
    verdict:str
    schema_version:str='cog020-v1'
    production_authorized:bool=False
    def __post_init__(self):
        for x in (self.record_id,self.source_component,self.reason_code):ident(x)
        hexhash(self.evidence_commitment)
        need(self.execution_status in ('EXECUTED','NOT_RUN','HISTORICAL'))
        need(self.verdict in ('PASS','PARTIAL','FAIL','BLOCKED','NOT_QUALIFIED'))
        need(self.schema_version=='cog020-v1' and self.production_authorized is False)
        if self.execution_status!='EXECUTED':need(self.verdict!='PASS')
    @property
    def commitment(self):self.__post_init__();return digest(self)

@dataclass(frozen=True)
class QualificationEvidence(QualificationCase):
    observation_json:str='{}'
    def __post_init__(self):
        super().__post_init__();need(type(self.observation_json) is str and len(self.observation_json.encode())<=32768)
        def pairs(ps):
            d={}
            for k,v in ps:need(k not in d);d[k]=v
            return d
        obj=json.loads(self.observation_json,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NUMBER')))
        need(type(obj) is dict and canonical(obj)==self.observation_json and digest(obj)==self.evidence_commitment)

@dataclass(frozen=True)
class QualificationFinding(QualificationCase):
    severity:str='P1'
    remediation:str='REVIEW'
    def __post_init__(self):
        super().__post_init__();need(self.severity in ('P1','P2'));ident(self.remediation);need(self.verdict!='PASS')

@dataclass(frozen=True)
class QualificationDomainResult(QualificationCase):
    evidence_ids:tuple=()
    def __post_init__(self):
        super().__post_init__();need(self.record_id in ('Q1','Q2','Q3','Q4','Q5','Q6'));need(type(self.evidence_ids) is tuple and 0<len(self.evidence_ids)<=64)
        for k in self.evidence_ids:ident(k)
        need(len(set(self.evidence_ids))==len(self.evidence_ids))

@dataclass(frozen=True)
class ReleaseCandidateDecision(QualificationCase):
    system_verdict:str='PARTIAL'
    eligibility:str='LOCAL_RC_NOT_ELIGIBLE'
    gates:tuple=()
    blockers:tuple=()
    def __post_init__(self):
        super().__post_init__();need(self.system_verdict in ('FULL','PARTIAL','BLOCKED','FAILED'))
        need(type(self.gates) is tuple and len(self.gates)==6 and all(type(x) is bool for x in self.gates))
        need(type(self.blockers) is tuple and len(self.blockers)<=64 and len(set(self.blockers))==len(self.blockers))
        for k in self.blockers:ident(k)
        ready=all(self.gates) and not self.blockers and self.system_verdict=='FULL'
        need(self.eligibility==('LOCAL_RC_ELIGIBLE' if ready else 'LOCAL_RC_NOT_ELIGIBLE'))
        if self.system_verdict=='FULL':need(ready)

@dataclass(frozen=True)
class QualificationReport(QualificationCase):
    cases:tuple=()
    evidence:tuple=()
    findings:tuple=()
    domains:tuple=()
    decision:object=None
    integrations:tuple=()
    def __post_init__(self):
        super().__post_init__();ids=set()
        for seq,cls in ((self.cases,QualificationCase),(self.evidence,QualificationEvidence),(self.findings,QualificationFinding),(self.domains,QualificationDomainResult)):
            need(type(seq) is tuple and len(seq)<=128)
            for r in seq:
                need(type(r) is cls);r.__post_init__();need(r.record_id not in ids);ids.add(r.record_id)
        need({d.record_id for d in self.domains}=={'Q'+str(i) for i in range(1,7)})
        emap={e.record_id:e for e in self.evidence}
        for d in self.domains:
            need(set(d.evidence_ids)<=set(emap));need(d.evidence_commitment==digest(tuple(emap[k].commitment for k in d.evidence_ids)))
        need(type(self.decision) is ReleaseCandidateDecision);self.decision.__post_init__()
        need(self.decision.blockers==tuple(f.record_id for f in self.findings if f.severity=='P1'))
        need(self.decision.evidence_commitment==digest(tuple(d.commitment for d in self.domains)))
        if self.decision.system_verdict=='FULL':need(all(d.verdict=='PASS' for d in self.domains))
        need(type(self.integrations) is tuple and len(self.integrations)==9)
        names=set()
        for pair in self.integrations:
            need(type(pair) is tuple and len(pair)==2);ident(pair[0]);need(pair[0] not in names);names.add(pair[0]);need(pair[1] in ('REAL_INTEGRATED','ISOLATED_ONLY','UNAVAILABLE','NOT_TESTED'))
        need(self.evidence_commitment==digest((tuple(e.commitment for e in self.evidence),tuple(f.commitment for f in self.findings),self.integrations)))

DEBT=(
('C15-001','P1','PRE_TOOL_TIMER'),('C15-002','P1','SHARED_SIMULATOR'),('C15-003','P1','CROSS_STORE_STOP'),('C15-004','P1','RECURSIVE_CYCLE'),('C15-005','P1','INTERRUPTED_RECOVERY'),('C15-006','P1','REPLAY_DEPENDENCIES'),('C15-007','P2','SCALE_TELEMETRY'),
('C16-R3-001','P1','ORIGINAL_QUALIFICATION'),('C16-R3-002','P1','STOP_GO_ATOMICITY'),('C16-R3-003','P2','SCALE_TELEMETRY'),
('C17-001','P1','PROVENANCE'),('C17-002','P1','INTEGRATION'),('C17-003','P1','ACTIVE_INTERRUPTION'),('C17-004','P1','OUTPUT_DTO'),
('C18-001','P1','INTEGRATION'),('C18-002','P1','ACTIVE_INTERRUPTION'),('C18-003','P2','SAMPLE_THRESHOLD'),('C18-004','P2','RATIONAL_COVERAGE'),
('C19-001','P1','MISSING_ADAPTERS'),('C19-002','P1','TRUSTED_SIGNALS'),('C19-003','P1','EVIDENCE_BINDING'),('C19-004','P2','DURABLE_RECOVERY'))

def fixture():
    e=ac.EvidenceReference('e','x',7,'observer',(),0,100,False)
    t=ac.VerificationTarget('target','producer','x',7,'DIRECT',('e',))
    v=u.VerificationInput(ac.VerificationRequest('vr',t,('e',),'local-structural-v1',100,0,100,False),(e,),(('e',ac.commitment(e)),))
    c=bm.BenchmarkCase('case','EXACT','INCONCLUSIVE',0,'author','ref')
    b=u.BenchmarkInput(bm.BenchmarkSuite('suite',(c,)),(),(bm.ObservationRecord('case','INCONCLUSIVE','observer','ref'),))
    inputs=(('a',v),('b',b));signals=((False,0),(False,1),(False,2))
    steps=(u.record(u.CognitiveStep,'a','request','verification',v,100,evidence=('e',)),u.record(u.CognitiveStep,'b','request','benchmark',b,100,('a',)))
    return [u.record(u.CognitiveRequest,'request','root','coordinator',inputs,1000),u.record(u.CognitiveContext,'context','request','coordinator',(signals,100),1000),steps,inputs,signals,100]

def run_signals(signals,deadline=100):
    a=fixture();a[4]=signals;a[5]=deadline;a[1]=replace(a[1],input_commitment=u.digest((signals,deadline)));return u.coordinate(*a)

def measured(answer='yes',confidence=F(4,5),state='ANSWER'):
    c=bm.BenchmarkCase('c','EXACT','yes',0,'author','ref');p=bm.PredictionRecord('c',answer,confidence,state,'candidate','ref');o=bm.ObservationRecord('c','yes','observer','ref')
    return bm.evaluate(bm.BenchmarkSuite('s',(c,)),(p,),(o,))

def rejects(fn):
    try:fn()
    except (ValueError,TypeError):return True
    return False

def qualify():
    a=fixture();first=u.coordinate(*a);second=u.coordinate(*a)
    a_bad=fixture();a_bad[2]=(replace(a_bad[2][0],input_commitment='0'*64),a_bad[2][1])
    forged=fixture();forged[2]=(replace(forged[2][0],evidence_refs=('fabricated',)),forged[2][1]);forged_result=u.coordinate(*forged)
    ref_binding_rejected=not any('fabricated' in r.evidence_refs for r in forged_result.results)
    malformed=av.verify(a[3][0][1].request,(),())
    stop=run_signals(((False,0),(False,1),(True,2)))
    deadline=run_signals(((False,0),(False,1),(False,2)),2)
    low=fixture();low[0]=replace(low[0],budget=0);budget=u.coordinate(*low)
    m=measured();extreme_rejected=rejects(lambda:measured(confidence=F(1,10**12)))
    obs=(
      ('architecture',{'registry':u.REGISTRY,'commitment_rejected':rejects(lambda:u.coordinate(*a_bad))}),
      ('integration',{'components':tuple(r.component for r in first.results),'status':first.verdict.status,'output_commitments':tuple(r.output_commitment for r in first.results)}),
      ('evidence',{'verification':first.results[0].verification,'malformed':malformed.status,'production':first.production_authorized,'promotion':first.promotion_authorized,'false_reference_rejected':ref_binding_rejected}),
      ('safety',{'stop':stop.verdict.status,'partial_results':len(stop.results),'deadline':deadline.verdict.status,'budget':budget.verdict.status}),
      ('determinism',{'equal':first==second,'commitment_equal':first.commitment==second.commitment,'durable_recovery':'NOT_QUALIFIED'}),
      ('measurement',{'brier':m.calibration.brier,'ece':m.calibration.ece,'accuracy':m.accuracy,'independence':m.independence,'valid_extreme_rejected':extreme_rejected}))
    evidence=tuple(QualificationEvidence('e-'+k,'COG017-019',digest(v),'EXECUTED','OBSERVED','PARTIAL',observation_json=canonical(v)) for k,v in obs)
    cases=tuple(QualificationCase('case-'+k,'COG017-019',digest(v),'EXECUTED','OBSERVED','PARTIAL') for k,v in obs)
    findings=tuple(QualificationFinding(k,k.split('-')[0],digest((k,s,r)),'HISTORICAL',r,'NOT_QUALIFIED',severity=s,remediation='INDEPENDENT_REQUALIFICATION') for k,s,r in DEBT)
    if not ref_binding_rejected:findings+=(QualificationFinding('C20-001','COG019',evidence[2].evidence_commitment,'EXECUTED','FALSE_EVIDENCE_REFERENCE_PROPAGATED','FAIL',severity='P1',remediation='EXACT_REFERENCE_BINDING'),)
    if extreme_rejected:findings+=(QualificationFinding('C20-002','COG018',evidence[5].evidence_commitment,'EXECUTED','VALID_RATIONAL_REJECTED','FAIL',severity='P2',remediation='OUTPUT_RATIONAL_BOUNDS'),)
    domains=tuple(QualificationDomainResult('Q'+str(i+1),'COG017-019',digest((e.commitment,)),'EXECUTED','LIMITED_LOCAL_QUALIFICATION','FAIL' if i==2 and not ref_binding_rejected else 'PARTIAL',evidence_ids=(e.record_id,)) for i,e in enumerate(evidence))
    critical=first.production_authorized or first.promotion_authorized or first.results[0].verification=='VERIFIED'
    decision=ReleaseCandidateDecision('release','COG020',digest(tuple(d.commitment for d in domains)),'EXECUTED','OPEN_GATES','FAIL' if critical else 'PARTIAL',system_verdict='FAILED' if critical else 'PARTIAL',gates=(False,False,True,False,False,False),blockers=tuple(f.record_id for f in findings if f.severity=='P1'))
    integrations=tuple((k,'REAL_INTEGRATED' if v=='AVAILABLE' else 'UNAVAILABLE') for k,v in u.REGISTRY)
    return QualificationReport('qualification','COG020',digest((tuple(e.commitment for e in evidence),tuple(f.commitment for f in findings),integrations)),'EXECUTED','BOUNDED_SCOPE','PARTIAL',cases=cases,evidence=evidence,findings=findings,domains=domains,decision=decision,integrations=integrations)

if __name__=='__main__':print(canonical(qualify()))
