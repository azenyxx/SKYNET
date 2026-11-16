"""Pure deterministic checks over bounded integer assertions, not natural-language reasoning.
Time is externally supplied; deadline is a logical checkpoint, not hard cancellation.
Evidence hashes establish identity only. Source authenticity is never inferred.
"""
from cognitive_adversarial_contracts import *
import hashlib

CATEGORIES=('CONTRADICTION','UNSUPPORTED','PROVENANCE','DEPENDENCY','INFERENCE','CONFLICT','TEMPORAL','UNCERTAINTY')

def verify(request, evidence, pins):
    findings=[]; used=0; target='invalid'; rc=''; sc=''
    challenges=tuple(AdversarialChallenge('c17:'+x,x) for x in CATEGORIES)
    def finish(status):
        return VerificationVerdict(target,status,tuple(c.challenge_id for c in challenges),request.evidence_refs if type(request) is VerificationRequest else (),tuple(findings),'cog017-local-structural-v1',used,rc,sc)
    def finding(category,code,ids=()):
        findings.append(VerificationFinding('c17:'+category,tuple(sorted(ids)),code))
    try:
        require(type(request) is VerificationRequest,'REQUEST'); request.__post_init__()
        target=request.target.target_id;rc=commitment(request)
        require(request.policy_id=='local-structural-v1','UNKNOWN_POLICY')
        if request.stop:
            finding('UNCERTAINTY','STOPPED');return finish('BLOCKED')
        if request.now>=request.deadline:
            finding('UNCERTAINTY','DEADLINE_EXHAUSTED');return finish('BLOCKED')
        require(type(evidence) is tuple and len(evidence)<=64,'SNAPSHOT')
        require(type(pins) is tuple and len(pins)<=64,'PINS')
        pinmap={}
        for item in pins:
            require(type(item) is tuple and len(item)==2,'PIN')
            k,v=item;ident(k)
            require(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None and k not in pinmap,'PIN')
            pinmap[k]=v
        by={}
        for e in evidence:
            require(type(e) is EvidenceReference,'EVIDENCE');e.__post_init__()
            require(e.evidence_id not in by,'DUPLICATE_EVIDENCE');by[e.evidence_id]=e
        sc=hashlib.sha256(b'SKYNET:COG017Snapshot:v1\0'+''.join(commitment(by[k]) for k in sorted(by)).encode()).hexdigest()
        # Fixed worst-case work accounting, checked before the bounded graph traversal.
        required=8+len(by)*4+sum(len(e.dependencies) for e in evidence)
        if required>request.max_checks:
            finding('UNCERTAINTY','RESOURCE_EXHAUSTED');return finish('BLOCKED')
        used=required
        require(set(by)==set(request.evidence_refs),'REFERENCE_MISMATCH')
        for e in sorted(evidence,key=lambda x:x.evidence_id):
            eid=(e.evidence_id,)
            if pinmap.get(e.evidence_id)!=commitment(e):finding('PROVENANCE','INTEGRITY_UNVERIFIED',eid)
            if e.source==request.target.producer:finding('PROVENANCE','SELF_EVIDENCE',eid)
            if e.superseded or request.now>e.expires_at or request.now<e.observed_at:finding('TEMPORAL','STALE_OR_FUTURE',eid)
            if not set(e.dependencies)<=set(by):finding('DEPENDENCY','MISSING_DEPENDENCY',eid)
        # Kahn elimination; no recursion, at most 64 rounds.
        pending=set(by);done=set()
        for _ in range(len(by)):
            ready={k for k in pending if set(by[k].dependencies)<=done}
            if not ready:break
            done|=ready;pending-=ready
        if pending:finding('DEPENDENCY','CIRCULAR_OR_MISSING',pending)
        t=request.target
        missing=set(t.dependencies)-set(by)
        if missing:finding('DEPENDENCY','MISSING_TARGET_DEPENDENCY',missing)
        if not t.dependencies:finding('UNSUPPORTED','NO_SUPPORT')
        values={}
        for e in evidence:values.setdefault(e.subject,set()).add(e.value)
        if any(len(v)>1 for v in values.values()):finding('CONFLICT','CONFLICTING_EVIDENCE',by)
        if t.subject in values and t.conclusion not in values[t.subject] and t.inference=='DIRECT':finding('CONTRADICTION','CONCLUSION_CONTRADICTED',by)
        if t.dependencies and not missing:
            selected=[by[k] for k in t.dependencies]
            if t.inference=='DIRECT':
                if len(selected)!=1 or selected[0].subject!=t.subject:finding('INFERENCE','INVALID_INFERENCE',t.dependencies)
                elif selected[0].value!=t.conclusion:finding('INFERENCE','INVALID_CONCLUSION',t.dependencies)
            elif sum(e.value for e in selected)!=t.conclusion:finding('INFERENCE','INVALID_CONCLUSION',t.dependencies)
        # No signature/pinned external origin contract exists here: pins are caller assertions.
        finding('UNCERTAINTY','INDEPENDENCE_NOT_ESTABLISHED')
        codes={f.reason_code for f in findings}
        if codes & {'INTEGRITY_UNVERIFIED','SELF_EVIDENCE','MISSING_DEPENDENCY','MISSING_TARGET_DEPENDENCY','CIRCULAR_OR_MISSING'}:return finish('BLOCKED')
        if codes & {'STALE_OR_FUTURE','CONFLICTING_EVIDENCE','NO_SUPPORT'}:return finish('INCONCLUSIVE')
        if codes & {'CONCLUSION_CONTRADICTED','INVALID_INFERENCE','INVALID_CONCLUSION'}:return finish('REFUTED')
        return finish('INCONCLUSIVE')
    except (ValueError,TypeError,AttributeError,KeyError,OverflowError):
        finding('UNCERTAINTY','INVALID_INPUT');return finish('BLOCKED')
    except Exception:
        finding('UNCERTAINTY','VERIFICATION_ERROR');return finish('ERROR')
