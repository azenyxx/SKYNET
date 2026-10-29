from cognitive_memory_contracts import *
def evaluate(proposal,pinned_dataset_commitment):
 require(type(proposal) is LearningProposalV1,'PROPOSAL_TYPE');proposal.__post_init__();p=proposal
 identifier(p.proposal_id);digest_text(pinned_dataset_commitment)
 require(p.dataset_commitment==pinned_dataset_commitment==commitment('Dataset',dict(ids=p.evaluation_ids,labels=p.labels)),'DATASET_BINDING')
 require(not set(p.training_ids)&set(p.evaluation_ids),'CONTAMINATION')
 require(1<=len(p.labels)<=128 and len(p.evaluation_ids)==len(p.labels)==len(p.baseline)==len(p.candidate),'WORKLOAD')
 require(len(set(p.evaluation_ids))==len(p.evaluation_ids),'DUPLICATE_SAMPLE')
 b=sum(a==z for a,z in zip(p.baseline,p.labels));c=sum(a==z for a,z in zip(p.candidate,p.labels));reg=sum(a==z and v!=z for a,v,z in zip(p.baseline,p.candidate,p.labels))
 status='REGRESSION_REJECTED' if reg else ('IMPROVEMENT_MEASURED' if c>b else 'NO_IMPROVEMENT')
 return LearningEvaluationV1(p.commitment,p.dataset_commitment,len(p.labels),b,c,reg,status)
def promote(*args,**kwargs):raise MemoryErrorV1('PROMOTION_AUTHORITY_UNAVAILABLE')
def rollback(*args,**kwargs):raise MemoryErrorV1('ROLLBACK_AUTHORITY_UNAVAILABLE')
