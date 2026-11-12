"""Local diagnostics only. Rational confidence; ten bins [i/10,(i+1)/10), last includes 1.
Brier measures confidence in answer correctness, not multiclass class probabilities.
Missing/invalid/abstained predictions count in accuracy denominator, not calibration.
STOP/deadline are preflight checks over supplied time, not hard interruption.
"""
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction as F
import hashlib,json,re

class BenchmarkError(ValueError): pass

def check(v,c='INVALID'):
    if not v: raise BenchmarkError(c)
def ident(v):check(type(v) is str and re.fullmatch(r'[a-zA-Z0-9_.:-]{1,96}',v) is not None)
def num(v):check(type(v) in (int,F) and abs(v)<=10**12 and (type(v) is int or v.denominator<=10**12))
def unit(v):num(v);check(0<=v<=1)
def count(v):check(type(v) is int and 0<=v<=10000)
def value(v):
    if type(v) is str:check(len(v.encode('utf-8'))<=4096)
    else:num(v)
def seq(v,t):
    check(type(v) is tuple and len(v)<=1000)
    for x in v:check(type(x) is t);x.__post_init__()
def canon(v):
    if is_dataclass(v):return {f.name:canon(getattr(v,f.name)) for f in fields(v)}
    if type(v) is F:return {'numerator':v.numerator,'denominator':v.denominator}
    if type(v) is tuple:return [canon(x) for x in v]
    return v
class DTO:
    @property
    def commitment(self):
        self.__post_init__()
        return hashlib.sha256(b'SKYNET:COG018:v1\0'+json.dumps(canon(self),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    def version(self):check(self.schema_version=='cog018-v1')

@dataclass(frozen=True)
class BenchmarkCase(DTO):
    case_id:str; category:str; expected:object; tolerance:object; author:str; provenance:str
    schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();ident(self.case_id);ident(self.author);ident(self.provenance)
        check(self.category in ('EXACT','NUMERIC'));value(self.expected);num(self.tolerance);check(self.tolerance>=0)
        if self.category=='NUMERIC':num(self.expected)
        else:check(self.tolerance==0)

@dataclass(frozen=True)
class BenchmarkSuite(DTO):
    suite_id:str; cases:tuple; policy_id:str='accuracy-v1'; schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();ident(self.suite_id);seq(self.cases,BenchmarkCase);check(0<len(self.cases)<=1000)
        check(len({x.case_id for x in self.cases})==len(self.cases));check(self.policy_id=='accuracy-v1')

@dataclass(frozen=True)
class PredictionRecord(DTO):
    case_id:str; answer:object; confidence:object; state:str; candidate:str; provenance:str
    schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();ident(self.case_id);ident(self.candidate);ident(self.provenance);unit(self.confidence)
        check(self.state in ('ANSWER','ABSTAIN','INVALID'))
        if self.state=='ANSWER':value(self.answer)
        else:check(self.answer is None and self.confidence==0)

@dataclass(frozen=True)
class ObservationRecord(DTO):
    case_id:str; outcome:object; source:str; provenance:str; schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();ident(self.case_id);ident(self.source);ident(self.provenance);value(self.outcome)

@dataclass(frozen=True)
class EvaluationResult(DTO):
    case_id:str; state:str; correct:int; confidence:object; schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();ident(self.case_id);check(self.state in ('ANSWER','ABSTAIN','INVALID','MISSING','NO_OBSERVATION'))
        check(type(self.correct) is int and self.correct in (0,1));unit(self.confidence)
        if self.state!='ANSWER':check(self.correct==0 and self.confidence==0)

@dataclass(frozen=True)
class CalibrationReport(DTO):
    samples:int; brier:object; ece:object; bins:tuple; overconfidence:object; underconfidence:object; sufficient:bool
    schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();count(self.samples);check(type(self.bins) is tuple and len(self.bins)==10)
        n=0
        for row in self.bins:
            check(type(row) is tuple and len(row)==3);count(row[0]);unit(row[1]);unit(row[2]);n+=row[0]
            if row[0]==0:check(row[1]==row[2]==0)
        check(n==self.samples)
        for x in (self.brier,self.ece,self.overconfidence,self.underconfidence):
            if self.samples:unit(x)
            else:check(x is None)
        check(type(self.sufficient) is bool and self.sufficient==(self.samples>=30))

@dataclass(frozen=True)
class BenchmarkRun(DTO):
    suite:BenchmarkSuite; results:tuple; calibration:CalibrationReport; accuracy:object; coverage:object; selective_accuracy:object; input_commitment:str
    independence:str='NOT_ESTABLISHED'; production_authorized:bool=False; schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();check(type(self.suite) is BenchmarkSuite);self.suite.__post_init__();seq(self.results,EvaluationResult)
        check(tuple(r.case_id for r in self.results)==tuple(c.case_id for c in self.suite.cases))
        check(type(self.calibration) is CalibrationReport);self.calibration.__post_init__()
        n=len(self.results);answered=[r for r in self.results if r.state=='ANSWER'];k=sum(r.correct for r in answered)
        unit(self.accuracy);unit(self.coverage);check(self.accuracy==F(k,n) and self.coverage==F(len(answered),n))
        if answered:unit(self.selective_accuracy);check(self.selective_accuracy==F(k,len(answered)))
        else:check(self.selective_accuracy is None)
        check(self.calibration==calibrate(answered));check(type(self.input_commitment) is str and re.fullmatch('[0-9a-f]{64}',self.input_commitment))
        check(self.independence=='NOT_ESTABLISHED' and self.production_authorized is False)

@dataclass(frozen=True)
class RegressionReport(DTO):
    status:str; findings:tuple; previous:str; current:str; schema_version:str='cog018-v1'
    def __post_init__(self):
        self.version();check(self.status in ('COMPARABLE','INCOMPARABLE'));check(type(self.findings) is tuple and len(self.findings)<=8 and len(set(self.findings))==len(self.findings))
        check(set(self.findings)<={'ACCURACY','CALIBRATION','ABSTENTION','INVALID','COVERAGE','MISSING','CALIBRATION_COVERAGE'})
        if self.status=='INCOMPARABLE':check(not self.findings)
        for x in (self.previous,self.current):check(type(x) is str and re.fullmatch('[0-9a-f]{64}',x))

def calibrate(rows):
    bins=[];n=len(rows)
    for i in range(10):
        group=[r for r in rows if min(int(r.confidence*10),9)==i]
        bins.append((len(group),sum((F(r.confidence) for r in group),F())/len(group) if group else F(),F(sum(r.correct for r in group),len(group)) if group else F()))
    if not n:return CalibrationReport(0,None,None,tuple(bins),None,None,False)
    brier=sum(((F(r.confidence)-r.correct)**2 for r in rows),F())/n
    ece=sum((F(k,n)*abs(c-a) for k,c,a in bins),F())
    delta=sum((F(r.confidence)-r.correct for r in rows),F())/n
    return CalibrationReport(n,brier,ece,tuple(bins),max(delta,F()),max(-delta,F()),n>=30)

def evaluate(suite,predictions,observations,*,budget=10000,stop=False,now=0,deadline=1):
    check(type(stop) is bool);count(budget);count(now);count(deadline)
    check(not stop,'STOPPED');check(now<deadline,'DEADLINE')
    check(type(suite) is BenchmarkSuite);suite.__post_init__();seq(predictions,PredictionRecord);seq(observations,ObservationRecord)
    check(budget>=12*len(suite.cases)+len(predictions)+len(observations),'BUDGET')
    ids={c.case_id for c in suite.cases};ps={p.case_id:p for p in predictions};obs={o.case_id:o for o in observations}
    check(len(ps)==len(predictions) and len(obs)==len(observations) and set(ps)<=ids and set(obs)<=ids,'BINDING')
    results=[]
    for c in suite.cases:
        p=ps.get(c.case_id);o=obs.get(c.case_id);state='MISSING' if p is None else p.state;correct=0;confidence=0
        if o is None:state='NO_OBSERVATION'
        else:check(type(o.outcome) is type(c.expected) and o.outcome==c.expected,'ANSWER_KEY_MISMATCH')
        if state=='ANSWER':
            confidence=p.confidence
            if c.category=='EXACT':correct=int(type(p.answer) is type(o.outcome) and p.answer==o.outcome)
            elif type(p.answer) not in (int,F):state='INVALID';confidence=0
            else:correct=int(abs(p.answer-o.outcome)<=c.tolerance)
        results.append(EvaluationResult(c.case_id,state,correct,confidence))
    rows=tuple(results);answered=[r for r in rows if r.state=='ANSWER'];k=sum(r.correct for r in answered);n=len(rows)
    binding=hashlib.sha256(b'SKYNET:COG018Inputs:v1\0'+(suite.commitment+''.join(ps[x].commitment for x in sorted(ps))+''.join(obs[x].commitment for x in sorted(obs))).encode()).hexdigest()
    return BenchmarkRun(suite,rows,calibrate(answered),F(k,n),F(len(answered),n),F(k,len(answered)) if answered else None,binding)

def compare(previous,current):
    for r in (previous,current):check(type(r) is BenchmarkRun);r.__post_init__()
    if previous.suite!=current.suite:return RegressionReport('INCOMPARABLE',(),previous.commitment,current.commitment)
    f=[]
    if current.accuracy<previous.accuracy:f.append('ACCURACY')
    a,b=previous.calibration,current.calibration
    if a.samples!=b.samples:f.append('CALIBRATION_COVERAGE')
    if a.samples and b.samples and (b.brier>a.brier or b.ece>a.ece):f.append('CALIBRATION')
    for state,code in (('ABSTAIN','ABSTENTION'),('INVALID','INVALID')):
        if sum(r.state==state for r in current.results)>sum(r.state==state for r in previous.results):f.append(code)
    if current.coverage!=previous.coverage:f.append('COVERAGE')
    if tuple(r.case_id for r in current.results if r.state in ('MISSING','NO_OBSERVATION'))!=tuple(r.case_id for r in previous.results if r.state in ('MISSING','NO_OBSERVATION')):f.append('MISSING')
    return RegressionReport('COMPARABLE',tuple(f),previous.commitment,current.commitment)
