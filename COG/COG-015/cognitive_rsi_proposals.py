from cognitive_rsi_contracts import *
from cognitive_rsi_diagnostics import diagnose
from cognitive_rsi_candidate import validate_candidate
DEFAULT={'RESOURCE':'MEMO','ACCURACY':'FAST','RESEARCH':'DISCRIMINATE','TRANSFER':'STRICT'}
def propose(b,observation,strategy=None,parent=None):
 bottleneck=diagnose(b,observation);strategy=DEFAULT[b.scenario] if strategy is None else strategy;pid=digest('ProposalID',dict(baseline=b.commitment,bottleneck=bottleneck.commitment,strategy=strategy));p=ImprovementProposalV1(b.namespace,b.session_id,(observation.commitment,),'TEST_ONLY',pid,b.commitment,bottleneck,strategy,('synthetic_fixture_only','no_runtime_activation'),'ANY_REGRESSION','RESTORE_LOCAL_SNAPSHOT')
 if parent is not None:validate_candidate(b,parent);require(parent.depth==0,'REFINEMENT_LIMIT');require(strategy!=parent.proposal.strategy,'NO_REFINEMENT')
 c=ImprovementCandidateV1(b.namespace,b.session_id,(p.commitment,),'TEST_ONLY',p,'0'*64 if parent is None else parent.commitment,0 if parent is None else 1,128,'HYPOTHESIZED');return validate_candidate(b,c)
