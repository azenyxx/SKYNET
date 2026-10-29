from cognitive_rsi_contracts import *
# Immutable local fixtures; qualification is synthetic, not authoritative telemetry.
FIXTURES=(('RESOURCE',(2,2,3,3),('4','4','9','9')),('ACCURACY',(2,3,4,5),('4','9','16','25')),('RESEARCH',(0,1),('LINEAR','LINEAR')),('TRANSFER',(0,1),('ACCEPT','ABSTAIN')))
CHALLENGE=(('RESOURCE',(4,4),('16','16')),('ACCURACY',(0,7),('0','49')),('RESEARCH',(2,),('LINEAR',)),('TRANSFER',(1,0,1),('ABSTAIN','ACCEPT','ABSTAIN')))
COMPONENTS=('4069ec1aa79bea69d14999abd2b303f56db47cb043580d77db895357348de7d6', '5933dc8c01bcf05305f50d5dd866ca4e3f37b10b1218913722f3e19ef645468a', '8df95d785c3c794c5670b6e5481f5745bba7ab572a79e1b095b5ef530197f112')
def fixture(scenario,challenge=False):
 for k,x,y in CHALLENGE if challenge else FIXTURES:
  if k==scenario:return x,y
 raise RSIError('SCENARIO')
def freeze(namespace,session_id,scenario):
 x,y=fixture(scenario);h=digest('Fixture',dict(scenario=scenario,inputs=x,labels=y,challenge=fixture(scenario,True)))
 return ImprovementBaselineV1(namespace,session_id,(h,),'TEST_ONLY',scenario,h,COMPONENTS,'NAME_ONLY' if scenario=='TRANSFER' else 'REPEAT','fixed-v1',0)
def validate_baseline(b):
 require(type(b) is ImprovementBaselineV1,'BASELINE_TYPE');require(b==freeze(b.namespace,b.session_id,b.scenario),'BASELINE_MISMATCH');return b
