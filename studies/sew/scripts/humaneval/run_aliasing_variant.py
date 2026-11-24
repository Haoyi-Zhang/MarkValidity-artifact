from pathlib import Path
import collections
import gzip
import hashlib
import importlib.util
import json
import sys
import argparse

parser=argparse.ArgumentParser()
for name in ('study-root','vendor','out'):
 parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.vendor.resolve()))
from sew import embed,detect
spec=importlib.util.spec_from_file_location('unchanged_original_executor',args.study_root.resolve()/'run_study.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
study=json.loads((args.study_root.resolve()/'study-spec.json').read_text())
out=args.out;out.mkdir(exist_ok=False);(out/'programs').mkdir()
rows=[];records=[]
for case in study['cases']:
 before=case['source'];ref=module.execute(before,study['input_domain'],10);records.append({'case_id':case['case_id'],'role':'reference',**ref})
 for key in study['keys']:
  k=bytes.fromhex(key['hex']);e=embed(before,'python',k);after=e.pop('code');d=detect(after,'python',k);a=module.execute(after,study['input_domain'],10)
  path='programs/'+case['case_id']+'__'+key['key_id']+'.py';(out/path).write_text(after)
  pairs=list(zip(ref['observations'],a['observations']));bad=[{'reference':l,'candidate':r}for l,r in pairs if l!=r]
  valid=a['compile_status']=='ok'and len(pairs)==len(study['input_domain'])and not bad
  rows.append({'case_id':case['case_id'],'key_id':key['key_id'],'embedding':e,'detector':d,'source_path':path,
   'candidate_sha256':hashlib.sha256(after.encode()).hexdigest(),'behavior_valid':valid,'detected':d['verdict']=='Watermark detected','mismatch_count':len(bad),'first_mismatch':bad[0]if bad else None})
  records.append({'case_id':case['case_id'],'key_id':key['key_id'],'role':'candidate',**a})
(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
with gzip.open(out/'observations.jsonl.gz','wt')as handle:
 for r in records:handle.write(json.dumps(r,sort_keys=True)+'\n')
summary={'status':'COMPLETE','scope':'Same targeted aliasing grid as prior stock study, with only the additional literal-predecessor S1 policy.',
 'configurations':len(rows),'behavior_valid':sum(r['behavior_valid']for r in rows),'detected':sum(r['detected']for r in rows),
 'joint':sum(r['detected']and r['behavior_valid']for r in rows),'native_calls':sum(len(r['observations'])for r in records),'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
