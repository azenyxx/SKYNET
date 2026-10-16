"""Pure conversion of freshly reverified artifacts to an isolated proposal."""
from cognitive_contracts import require
from cognitive_verification_contracts import VerificationRequestV1
from cognitive_evidence_verifier import verify_original_evidence
from cognitive_tool_contracts import request_commitment
from cognitive_knowledge_contracts import (
    KnowledgeCategory, KnowledgeEvidenceRefV1, ComputedHashFactV1,
    KnowledgeProposalV1, KnowledgeDecisionV1,
)

def _reject(reason, dependency=False):
    return KnowledgeDecisionV1('cog-knowledge-decision-v1',
        'KNOWLEDGE_DEPENDENCY_UNAVAILABLE' if dependency else 'KNOWLEDGE_REJECTED',
        reason,None,False,False,False)

def propose_knowledge(original: VerificationRequestV1, *,
                      category: KnowledgeCategory='COMPUTED_FACT_ISOLATED',
                      provenance: str='ISOLATED_COMPUTATION_UNTRUSTED_ORIGIN') -> KnowledgeDecisionV1:
    if type(category) is not str or category!='COMPUTED_FACT_ISOLATED':
        return _reject('CLASSIFICATION_FORBIDDEN')
    if type(provenance) is not str or provenance!='ISOLATED_COMPUTATION_UNTRUSTED_ORIGIN':
        return _reject('INVALID_PROVENANCE')
    if type(original) is not VerificationRequestV1:
        return _reject('INVALID_ORIGINAL_ARTIFACTS')
    # Never accept an already positive VerificationDecisionV1 as evidence.
    decision=verify_original_evidence(original)
    if decision.status=='VERIFICATION_DEPENDENCY_UNAVAILABLE':
        return _reject('MISSING_DEPENDENCY',True)
    if decision.status!='EVIDENCE_VERIFIED_ISOLATED':
        return _reject('VERIFICATION_REJECTED')
    require(not decision.production_authorized and not decision.trusted_verification
            and not decision.task_completion_authorized,'TRUST_BOUNDARY')
    r,e=original.request,original.evidence
    require(decision.original_evidence_commitment==e.commitment and
            decision.original_request_commitment==request_commitment(r),'VERIFICATION_BINDING')
    ref=KnowledgeEvidenceRefV1('cog-knowledge-evidence-ref-v1',
        r.canonical_input_digest,decision.original_request_commitment,
        e.result.commitment,e.commitment,decision.verification_id,provenance)
    fact=ComputedHashFactV1('cog-computed-hash-fact-v1','SHA256_OF_UTF8_INPUT',
        r.canonical_input_digest,e.result.sha256_hex,e.result.input_byte_length)
    proposal=KnowledgeProposalV1('cog-knowledge-proposal-v1',r.task_id,r.plan_id,
        r.step_id,r.request_id,r.progress_revision,category,provenance,fact,ref,1,False,False,False)
    return KnowledgeDecisionV1('cog-knowledge-decision-v1','KNOWLEDGE_PROPOSED_ISOLATED',
        'ISOLATED_RELATION_ONLY',proposal,False,False,False)
