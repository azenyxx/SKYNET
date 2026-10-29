"""Bounded local integration; no capability, persistence or provenance authority.
Boundary signals are caller-supplied snapshots, not authenticated clock/STOP sources.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
from fractions import Fraction
import hashlib,json,re
import cognitive_adversarial_contracts as ac
import cognitive_adversarial_verifier as av
import cognitive_benchmark as bm

class IntegrationError(ValueError):pass

def require(v,code='INVALID'):
    if not v:raise IntegrationError(code)
def ident(v):require(type(v) is str and re.fullmatch('[A-Za-z0-9_.:-]{1,96}',v) is not None)
def integer(v):require(type(v) is int and 0<=v<=10000)
def refs(v):
    require(type(v) is tuple and len(v)<=32)
    for x in v:ident(x)
    require(len(set(v))==len(v))
def canonical(v):
    if is_dataclass(v):return {f.name:canonical(getattr(v,f.name)) for f in fields(v)}
    if type(v) is Fraction:return [v.numerator,v.denominator]
    if type(v) is tuple:return [canonical(x) for x in v]
    return v
def digest(v):return hashlib.sha256(b'SKYNET:COG019:v1\0'+json.dumps(canonical(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class Record:
    record_id:str
    parent:str
    dependencies:tuple
    component:str
    input_commitment:str
    output_commitment:str
    status:str
    evidence_refs:tuple
    verification:str
    budget:int
    reasons:tuple
    schema_version:str='cog019-v1'
    def __post_init__(self):
        for x in (self.record_id,self.parent,self.component):ident(x)
        refs(self.dependencies);refs(self.evidence_refs);refs(self.reasons);integer(self.budget)
        for x in (self.input_commitment,self.output_commitment):require(type(x) is str and re.fullmatch('[0-9a-f]{64}',x) is not None)
        require(self.schema_version=='cog019-v1')
        require(self.status in ('REQUEST','VALIDATED','PLANNED','DISPATCHED','COLLECTED','VERIFICATION','AGGREGATED','DIAGNOSTIC','BLOCKED','ERROR','STOPPED','DEADLINE','BUDGET'))
        require(self.verification in ('NOT_ESTABLISHED','INCONCLUSIVE','REFUTED','BLOCKED','ERROR','STRUCTURAL_ONLY'))
    @property
    def commitment(self):self.__post_init__();return digest(self)

@dataclass(frozen=True)
class CognitiveRequest(Record):pass
@dataclass(frozen=True)
class CognitiveContext(Record):pass
@dataclass(frozen=True)
class CognitiveStep(Record):pass
@dataclass(frozen=True)
class CognitiveResult(Record):pass
@dataclass(frozen=True)
class CognitiveTrace(Record):pass
@dataclass(frozen=True)
class IntegrationVerdict(Record):pass

@dataclass(frozen=True)
class VerificationInput:
    request:ac.VerificationRequest
    evidence:tuple
    pins:tuple
    def validate(self):
        require(type(self.request) is ac.VerificationRequest);self.request.__post_init__()
        require(type(self.evidence) is tuple and len(self.evidence)<=32)
        for e in self.evidence:require(type(e) is ac.EvidenceReference);e.__post_init__()
        require(type(self.pins) is tuple and len(self.pins)<=32)
        for p in self.pins:
            require(type(p) is tuple and len(p)==2);ident(p[0]);require(type(p[1]) is str and re.fullmatch('[0-9a-f]{64}',p[1]) is not None)

@dataclass(frozen=True)
class BenchmarkInput:
    suite:bm.BenchmarkSuite
    predictions:tuple
    observations:tuple
    def validate(self):
        require(type(self.suite) is bm.BenchmarkSuite);self.suite.__post_init__();require(len(self.suite.cases)<=32)
        for group,kind in ((self.predictions,bm.PredictionRecord),(self.observations,bm.ObservationRecord)):
            require(type(group) is tuple and len(group)<=32)
            for r in group:require(type(r) is kind);r.__post_init__()

REGISTRY=(('verification','AVAILABLE'),('benchmark','AVAILABLE'),('memory','UNAVAILABLE'),('world','UNAVAILABLE'),('metacognition','UNAVAILABLE'),('discovery','UNAVAILABLE'),('transfer','UNAVAILABLE'),('improvement','UNAVAILABLE'),('parallel','UNAVAILABLE'))
def component_status(name):
    ident(name)
    for k,v in REGISTRY:
        if k==name:return v
    raise IntegrationError('UNKNOWN_COMPONENT')

def record(cls,rid,parent,component,payload,budget,dependencies=(),evidence=()):
    return cls(rid,parent,dependencies,component,digest(payload),digest(()),'REQUEST',evidence,'NOT_ESTABLISHED',budget,())

def order(steps):
    require(type(steps) is tuple and 0<len(steps)<=32)
    by={}
    for s in steps:
        require(type(s) is CognitiveStep);s.__post_init__();require(s.record_id not in by,'DUPLICATE');by[s.record_id]=s
    for s in steps:require(set(s.dependencies)<=set(by),'MISSING_DEPENDENCY')
    pending=set(by);done=[]
    for _ in steps:
        ready=sorted(k for k in pending if set(by[k].dependencies)<=set(done))
        require(ready,'CYCLE');k=ready[0];done.append(k);pending.remove(k)
    return tuple(by[k] for k in done)

@dataclass(frozen=True)
class Outcome:
    verdict:IntegrationVerdict
    results:tuple
    outputs:tuple
    trace:tuple
    production_authorized:bool=False
    promotion_authorized:bool=False
    def __post_init__(self):
        require(type(self.verdict) is IntegrationVerdict);self.verdict.__post_init__()
        require(type(self.results) is tuple and type(self.outputs) is tuple and len(self.results)==len(self.outputs)<=32)
        for r in self.results:require(type(r) is CognitiveResult);r.__post_init__()
        require(type(self.trace) is tuple and len(self.trace)<=200)
        for t in self.trace:require(type(t) is CognitiveTrace);t.__post_init__()
        for r,o in zip(self.results,self.outputs):require(r.output_commitment==digest(o))
        require(self.production_authorized is False and self.promotion_authorized is False)
    @property
    def commitment(self):return digest(self)

def coordinate(request,context,steps,inputs,signals,deadline):
    """Signals: explicit (stop, logical_time) for preflight and each step boundary.
    No replay ledger, hard interruption, restart recovery or trusted aggregation.
    """
    require(type(request) is CognitiveRequest and type(context) is CognitiveContext)
    request.__post_init__();context.__post_init__();integer(deadline)
    require(request.status==context.status=='REQUEST' and request.verification==context.verification=='NOT_ESTABLISHED')
    require(context.parent==request.record_id and request.component==context.component=='coordinator','CONTEXT')
    ordered=order(steps)
    require(type(inputs) is tuple and len(inputs)==len(steps))
    by={}
    for pair in inputs:
        require(type(pair) is tuple and len(pair)==2);key,payload=pair;ident(key);require(key not in by,'DUPLICATE_INPUT')
        require(type(payload) in (VerificationInput,BenchmarkInput));payload.validate();by[key]=payload
    require(set(by)=={s.record_id for s in steps},'INPUT_BINDING')
    require(request.input_commitment==digest(tuple(sorted(inputs,key=lambda x:x[0]))),'REQUEST_BINDING')
    require(type(signals) is tuple and len(signals)==len(steps)+1)
    prev=0
    for signal in signals:
        require(type(signal) is tuple and len(signal)==2 and type(signal[0]) is bool);integer(signal[1]);require(signal[1]>=prev);prev=signal[1]
    require(context.input_commitment==digest((signals,deadline)),'SIGNAL_BINDING')
    for s in ordered:
        require(s.parent==request.record_id and s.status=='REQUEST' and s.verification=='NOT_ESTABLISHED','STEP_BINDING')
        require(s.input_commitment==digest(by[s.record_id]),'INPUT_BINDING')
        require(component_status(s.component)=='AVAILABLE','UNAVAILABLE')
        require((s.component=='verification' and type(by[s.record_id]) is VerificationInput) or (s.component=='benchmark' and type(by[s.record_id]) is BenchmarkInput),'ADAPTER')
    trace=[];results=[];outputs=[];produced={};used=0
    def event(status,step=None,out=None):
        base=request if step is None else step
        trace.append(CognitiveTrace('event'+str(len(trace)),request.record_id,base.dependencies,base.component,base.input_commitment,digest(out),status,base.evidence_refs,'NOT_ESTABLISHED',used,()))
    def terminal(status,reason):
        v=IntegrationVerdict('verdict',request.record_id,(), 'coordinator',request.input_commitment,digest(tuple(results)),status,request.evidence_refs,'NOT_ESTABLISHED',used,(reason,))
        return Outcome(v,tuple(results),tuple(outputs),tuple(trace))
    event('REQUEST')
    if signals[0][0]:return terminal('STOPPED','STOP')
    if signals[0][1]>=deadline:return terminal('DEADLINE','DEADLINE')
    event('VALIDATED');event('PLANNED')
    for index,s in enumerate(ordered):
        stop,now=signals[index+1]
        if stop:return terminal('STOPPED','STOP')
        if now>=deadline:return terminal('DEADLINE','DEADLINE')
        if used+s.budget>min(request.budget,context.budget):return terminal('BUDGET','EXHAUSTED')
        used+=s.budget;event('DISPATCHED',s)
        try:
            p=by[s.record_id]
            if s.component=='verification':
                require(s.budget>=p.request.max_checks,'COMPONENT_BUDGET')
                out=av.verify(replace(p.request,now=now,deadline=min(deadline,p.request.deadline)),p.evidence,p.pins)
                require(type(out) is ac.VerificationVerdict and out.production_authorized is False and out.promotion_authorized is False and out.independence=='NOT_ESTABLISHED','TRUST')
                require(out.status in ('INCONCLUSIVE','REFUTED','BLOCKED','ERROR'),'TRUST')
                verification=out.status
            else:
                predictions=p.predictions
                if s.dependencies:
                    require(len(s.dependencies)==1 and len(p.suite.cases)==1,'COMBINED_SHAPE')
                    prior=produced[s.dependencies[0]];require(type(prior) is ac.VerificationVerdict,'COMBINED_SOURCE')
                    require(not predictions,'OVERRIDE')
                    predictions=(bm.PredictionRecord(p.suite.cases[0].case_id,prior.status,0,'ANSWER','cog017',prior.verdict_id),)
                out=bm.evaluate(p.suite,predictions,p.observations,budget=s.budget,now=now,deadline=deadline)
                out.__post_init__();verification='NOT_ESTABLISHED'
            event('COLLECTED',s,out);event('VERIFICATION',s,out)
            results.append(CognitiveResult(s.record_id,request.record_id,s.dependencies,s.component,s.input_commitment,digest(out),'DIAGNOSTIC',s.evidence_refs,verification,s.budget,('LOCAL_DIAGNOSTIC',)))
            outputs.append(out);produced[s.record_id]=out
            if verification in ('BLOCKED','ERROR'):return terminal('BLOCKED','COMPONENT_REJECTED')
        except Exception:
            event('ERROR',s);return terminal('ERROR','COMPONENT_ERROR')
    event('AGGREGATED',out=tuple(results));return terminal('DIAGNOSTIC','NO_TRUSTED_PROMOTION')
