#!/usr/bin/env python3
"""Export only pre-audit inputs; no candidate labels or observations survive."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS = ('dataset','task_id','variant','key_id','key_hex','detected','suite_cost',
          'reference_sha256','candidate_sha256','contract_sha256','source_contract_sha256')

def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--ledger',nargs=2,action='append',required=True,metavar=('ROWS','ASSET_ROOT'))
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();root=a.artifact.resolve()
    if a.out.exists():raise ValueError('choose a new output file')
    public=[];groups={};inputs=[]
    for index,(rpath,asset) in enumerate(a.ledger):
        rp=Path(rpath).resolve();base=Path(asset).resolve()
        records=json.loads(rp.read_text());refs={}
        if (base/'references.json').exists():
            refs={(r['task_id'],r['reference_sha256'],r['contract_sha256']):r
                  for r in json.loads((base/'references.json').read_text())}
        def relative(path):
            result=(base/path).resolve()
            if not result.is_relative_to(root):raise ValueError('public asset outside artifact')
            return result.relative_to(root).as_posix()
        for ri,r in enumerate(records):
            item={k:r[k] for k in FIELDS}
            if type(item['detected']) is not bool:raise ValueError('unknown detector event')
            if type(item['suite_cost']) is not int or item['suite_cost']!=1:raise ValueError('unsupported suite cost')
            identity={k:r[k] for k in ('reference_sha256','candidate_sha256','contract_sha256')}
            if hashlib.sha256(canonical(identity)).hexdigest()!=r['source_contract_sha256']:
                raise ValueError('row identity does not match source hashes')
            item.update(input_index=index,row_index=ri)
            public.append(item)
            ref=refs.get((r['task_id'],r['reference_sha256'],r['contract_sha256']),{})
            ref_obs=r.get('reference_observation_path',ref.get('observations_path'))
            ref_sha=r.get('reference_observation_sha256',ref.get('observations_sha256'))
            if not ref_obs or not ref_sha:raise ValueError('missing reference setup evidence')
            meta=dict(dataset=r['dataset'],task_id=r['task_id'],
                      reference_sha256=r['reference_sha256'],candidate_sha256=r['candidate_sha256'],
                      contract_sha256=r['contract_sha256'],
                      source_file=relative(r['source_path']),
                      reference_file=relative(r.get('reference_path',ref.get('source_path',f"sources/{r['reference_sha256']}.py"))),
                      contract_file=relative(r.get('contract_path',f"contracts/{r['contract_sha256']}.json")),
                      reference_observation_file=relative(ref_obs),reference_observation_sha256=ref_sha)
            g=r['source_contract_sha256'];old=groups.get(g)
            if old:
                for f in ('reference_sha256','candidate_sha256','contract_sha256','dataset','task_id'):
                    if old[f]!=meta[f]:raise ValueError('group metadata collision')
            else:groups[g]=meta
        inputs.append(dict(rows_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),rows=len(records)))
    output=dict(schema='markvalidity-public-native-audit-v1',fields=list(FIELDS),
                disclosure='Candidate validity, candidate observation paths, elapsed times and observed invocation counts are absent. Reference setup evidence is public.',
                inputs=inputs,rows=public,groups=groups)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'rows':len(public),'groups':len(groups),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
