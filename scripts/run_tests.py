import os,sys,subprocess,json,time,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.chdir(root)
paths=[root/'src']+sorted((root/'tests/unit').iterdir());env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,paths)))
groups=sys.argv[1:] or ['sys%03d'%i for i in range(1,9)]+['recovery','e2e']
results=[]
for group in groups:
 directory='tests/unit/'+group if group.startswith('sys') else 'tests/'+group
 env['PYTHONPATH']=os.pathsep.join(map(str,[root/directory,root/'src',root/'tests/unit/sys005',root/'tests/unit/sys006']));stats=root/'audit'/('COUNTS-'+group+'.json');stats.unlink(missing_ok=True);command=[sys.executable,'scripts/test_suite.py',directory,str(stats)];start=time.monotonic()
 try:
  p=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=260);output=p.stdout;code=p.returncode
 except subprocess.TimeoutExpired as e:output=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else (e.stdout or '');output+='\nTIMEOUT\n';code=124
 (root/'audit/raw'/f'{group}.txt').write_text(output);lines=output.splitlines();ran=re.findall(r'Ran (\d+) tests?',output)
 result=dict(suite=group,command=command,cwd=str(root),exit_code=code,seconds=time.monotonic()-start,collected=int(ran[-1]) if ran else None,PASS=sum(x.endswith(' ... ok') for x in lines),FAIL=sum(x.endswith(' ... FAIL') for x in lines),ERROR=sum(x.endswith(' ... ERROR') for x in lines),SKIP=sum(' ... skipped ' in x for x in lines));result.update(json.loads(stats.read_text()) if stats.exists() else {'collected':0,'PASS':0,'FAIL':0,'ERROR':1,'SKIP':0,'collection_or_process_error':True});results.append(result);print(json.dumps(result),flush=True)
 (root/'audit'/('RESULTS-'+group+'.json')).write_text(json.dumps(result,indent=2))
(root/'audit/LAST-RUN.json').write_text(json.dumps(results,indent=2));sys.exit(any(x['exit_code'] for x in results))
