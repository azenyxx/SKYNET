from cognitive_rsi_contracts import *
from cognitive_rsi_baseline import validate_baseline
ALLOWED={'RESOURCE':('MEMO','FAST'),'ACCURACY':('FAST','MEMO'),'RESEARCH':('DISCRIMINATE',),'TRANSFER':('STRICT',)}
def validate_candidate(b,c):
 validate_baseline(b);require(type(c) is ImprovementCandidateV1,'CANDIDATE_TYPE');c.__post_init__();p=c.proposal
 require((b.namespace,b.session_id)==(c.namespace,c.session_id)==(p.namespace,p.session_id)==(p.bottleneck.namespace,p.bottleneck.session_id),'SCOPE');require(p.baseline_commitment==b.commitment,'BASELINE_BINDING');require(p.strategy in ALLOWED[b.scenario],'STRATEGY');require(p.proposal_id==digest('ProposalID',dict(baseline=b.commitment,bottleneck=p.bottleneck.commitment,strategy=p.strategy)),'PROPOSAL_BINDING');require((c.depth==0 and c.parent_commitment=='0'*64) or (c.depth==1 and c.parent_commitment!='0'*64),'PARENT');return c
