from fractions import Fraction
from cognitive_meta_contracts import *
def assess_uncertainty(trace,findings):
 codes=tuple(sorted({f.code for f in findings}));kind='CONTRADICTED' if 'CONTRADICTION' in codes else ('UNKNOWN' if codes else 'MODEL_RELATIVE')
 return MetaUncertaintyV1(trace.namespace,trace.trace_id,trace.timestamp,'MONITOR',(trace.commitment,),'INFERRED','UNVERIFIED',kind,codes)
def calibration(probabilities,labels,namespace='test',trace_id='calibration'):
 require(type(probabilities) is tuple and type(labels) is tuple and 1<=len(labels)<=1000 and len(probabilities)==len(labels),'CALIBRATION_INPUT')
 bins={};brier=Fraction(0);covered=0
 for p,y in zip(probabilities,labels):
  require(type(y) is int and y in (0,1),'LABEL')
  if p is None:continue
  require(type(p) is int and 0<=p<=1000,'PROBABILITY');covered+=1;brier+=(Fraction(p,1000)-y)**2;bins.setdefault(min(p//100,9),[]).append((p,y))
 require(covered>0,'NO_COVERAGE');brier/=covered;ece=Fraction(0)
 for pairs in bins.values():ece+=abs(sum(Fraction(p,1000)-y for p,y in pairs))/covered
 return MetaConfidenceAssessmentV1(namespace,trace_id,0,'MONITOR',(),'INFERRED','UNVERIFIED',len(labels),covered,brier.numerator,brier.denominator,ece.numerator,ece.denominator,'SYNTHETIC_FIXTURE_ONLY')
