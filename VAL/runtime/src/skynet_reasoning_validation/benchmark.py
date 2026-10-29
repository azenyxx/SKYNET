from .contracts import validate,hashcheck
SEEDS=(1001,2003)
def rename(e,suffix):return e+suffix if type(e)is str else [e[0]]+[rename(x,suffix) for x in e[1:]]
def equivalent(e):
 if type(e)is str:return e
 if e[0]=='implies':return ['or',['not',equivalent(e[1])],equivalent(e[2])]
 return [e[0]]+[equivalent(x) for x in e[1:]]
def generate(partition,freeze=None):
 phase=('development','validation','holdout').index(partition)
 if partition=='holdout':hashcheck(freeze)
 out=[]
 for d in range(1,9):
  for mode in range(3):
   seed=SEEDS[mode%2] if phase<2 else (4099,7919)[mode%2]
   v=lambda i:'p'+str(i)+'s'+str(seed)+'n'+str(phase)
   n=phase+3;a,b,c=v(0),v(1),v(2)
   premises=[a,['implies',a,b]];query=b
   if d==1:
    query=[('and','or','iff')[phase],a,b];premises=[a,b]
   elif d==2 and phase==1:premises=[['implies',a,b],['not',b]];query=['not',a]
   elif d in (2,4,5,8):
    premises=[v(0)]+[['implies',v(i),v(i+1)] for i in range(n)];query=v(n)
    if d==8:premises+=[['or',v(1),v(2)],['iff',v(n),v(n+1)]];query=['and',v(n),v(n+1)]
   elif d==3:premises=[['or',a,b],['not',['and',a,b]],['not',b]];query=a
   elif d==6:premises=[['implies',a,b]];query=b
   elif d==7:premises=[['not',['not',a]],['implies',a,b]];query=['or',b,['not',b]]
   if mode==0:
    if d==5:premises += [['not',query]]
    else:premises += [a,['not',a]]
   elif mode==1:
    if d==2:premises=[['implies',a,b],b];query=a
    else:query=v(7)
   elif d==6:premises+=[a]
   for variant in range(2):
    t={'schema':'val002-v1','case_id':'R-%03d-%s-%d-%d'%(d,partition,mode,variant),'domain':'R-%03d'%d,'partition':partition,'seed':seed,'difficulty':('basic','intermediate','advanced')[mode],'pair_id':'R-%03d-%s-%d'%(d,partition,mode),'premises':premises if variant==0 else [equivalent(rename(e,'x')) for e in reversed(premises)],'query':query if variant==0 else ['not',['not',rename(query,'x')]]};validate(t);out.append(t)
 return out
