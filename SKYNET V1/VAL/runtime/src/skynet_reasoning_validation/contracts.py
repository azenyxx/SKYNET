from skynet_validation.evidence import canonical,commitment,need,ident,hashcheck
DOMAINS=tuple('R-%03d'%i for i in range(1,9))
OPS={'not':1,'and':2,'or':2,'implies':2,'iff':2}
def variables(expr,depth=0):
 need(depth<=8,'LOGIC_DEPTH')
 if type(expr)is str:ident(expr);return {expr}
 need(type(expr)is list and len(expr)>=1 and type(expr[0])is str and expr[0]in OPS,'EXPRESSION');need(len(expr)==OPS[expr[0]]+1,'ARITY');out=set()
 for x in expr[1:]:out.update(variables(x,depth+1))
 return out
def validate(t):
 need(type(t)is dict and set(t)=={'schema','case_id','domain','partition','seed','difficulty','pair_id','premises','query'},'TASK_FIELDS');need(t['schema']=='val002-v1','SCHEMA');ident(t['case_id']);ident(t['pair_id']);need(t['domain']in DOMAINS,'DOMAIN');need(t['partition']in('development','validation','holdout'),'PARTITION');need(type(t['seed'])is int and 0<=t['seed']<=1000000,'SEED');need(t['difficulty']in('basic','intermediate','advanced'),'DIFFICULTY');need(type(t['premises'])is list and len(t['premises'])<=16,'PREMISES');vs=variables(t['query'])
 for x in t['premises']:vs.update(variables(x))
 need(len(vs)<=8,'VARIABLE_BOUND');canonical(t);return sorted(vs)
