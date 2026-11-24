"""Resolve declared third-party imports with paired fresh native observations."""
import ast,datetime,hashlib,importlib.metadata,importlib.util,json,os,pathlib,platform,re,subprocess,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parent
ARTIFACT=ROOT.parents[2]/'work/MarkValidity_TOSEM/artifact'
# Derive the shared workspace robustly from this task-local location.
ARTIFACT=ROOT.parents[2]/'work/MarkValidity_TOSEM/artifact'
if not ARTIFACT.exists():raise ValueError(str(ARTIFACT))
sys.path.insert(0,str(ARTIFACT/'external-studies/sew_natural/comparison_costs'))
import admission
OUT=ROOT/'dependency-contracts'
if OUT.exists():raise ValueError('fresh output required')
OUT.mkdir()
incidence=[];selected=[]
for cohort in ['gpt4o','qwen']:
 tasks=json.loads((ROOT/'validated'/cohort/'tasks.json').read_text())
 rows={(r['dataset'],str(r['task_id'])):r for r in json.loads((ROOT/'validated'/cohort/'results.json').read_text())}
 for task in tasks:
  modules=set()
  for line in (task.get('context_prompt','')+task['source']).splitlines():
   match=re.match(r'^\s*from\s+([\w.]+)\s+import\s',line)
   if match:modules.add(match.group(1).split('.')[0])
   match=re.match(r'^\s*import\s+(.+)',line)
   if match:
    for part in match.group(1).split(','):modules.add(part.strip().split()[0].split('.')[0])
  external=sorted(x for x in modules if x not in sys.stdlib_module_names and x!='__future__')
  incidence.append({'cohort':cohort,'dataset':task['dataset'],'task_id':task['task_id'],'imports':sorted(modules),'external':external})
  if external:selected.append((cohort,task,rows[(task['dataset'],str(task['task_id']))],external))
assert [(c,t['task_id'],m) for c,t,r,m in selected]==[('gpt4o','HumanEval/150',['sympy']),('qwen','HumanEval/32',['numpy'])]
packages={m:importlib.metadata.version(m) for c,t,r,modules in selected for m in modules}
assert all(importlib.util.find_spec(m) for m in packages)
protocol={'status':'FIXED_BEFORE_EXECUTION','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_scan_rows':len(incidence),'selection':'All declared non-standard-library imports in the complete two-cohort input population, before paired reexecution. No selection by candidate result.','packages':packages,'invocation_flags':['-B'],'pythonpath_removed':True,'native_observer':'unchanged benchmark observer','contracts':[{k:v for k,v in x.items()} for x in incidence if x['external']]}
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(OUT/'import-incidence.json').write_text(json.dumps(incidence,indent=2)+'\n')
records=[]
for cohort,task,row,dependencies in selected:
 for side in ['reference','candidate']:
  previous=row[side+'_native'];request=previous['execution_request'];runner=ARTIFACT/previous['observer_file']
  env=os.environ.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONOPTIMIZE',None)
  env.update(PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  start=time.monotonic();interruption=None
  with tempfile.TemporaryDirectory(prefix='crest-dependency-') as tmp:
   try:
    result=subprocess.run([sys.executable,'-B',str(runner)],cwd=tmp,env=env,input=json.dumps(request),text=True,capture_output=True,timeout=15)
    stdout,stderr,returncode=result.stdout,result.stderr,result.returncode
   except subprocess.TimeoutExpired as exc:
    stdout,stderr,returncode=exc.stdout or '',exc.stderr or '',None
    if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
    if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
    interruption='wall_timeout'
  try:label=admission.humaneval(stdout,returncode,interruption);rejected=None
  except admission.EvidenceRejected as exc:label=None;rejected=str(exc)
  native={'label':label,'evidence_rejected':rejected,'stdout':stdout,'stderr':stderr,'returncode':returncode,'interruption':interruption,'elapsed_seconds':time.monotonic()-start,'execution_request':request,'observer_source_sha256':hashlib.sha256(runner.read_bytes()).hexdigest(),'observer_file':str(runner.relative_to(ARTIFACT)),'execution_environment':{'python':sys.version,'platform':platform.platform(),'hash_seed':'0','optimization_disabled':True,'wall_timeout_seconds':15,'cpu_seconds':10,'address_space_bytes':1073741824,'invocation_flags':['-B'],'site_initialization':'enabled','pythonpath_removed':True,'declared_dependencies':{m:packages[m] for m in dependencies}}}
  records.append({'cohort':cohort,'dataset':task['dataset'],'task_id':task['task_id'],'side':side,'native':native})
  print(json.dumps({'cohort':cohort,'task_id':task['task_id'],'side':side,'label':label,'error':json.loads(stdout).get('error') if stdout else None}),flush=True)
(OUT/'receipts.json').write_text(json.dumps(records,indent=2)+'\n')
