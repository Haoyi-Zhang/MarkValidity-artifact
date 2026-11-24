#!/usr/bin/env python3
"""Full-corpus catalogue ablation; detector and thresholds remain unchanged."""
import argparse
import concurrent.futures
import datetime
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import run_crest_study as base

OMIT=(20,24,38,46)


def initialize(upstream,artifact,output):
    base.initialize(upstream,artifact,output)
    import transformations
    catalogue=dict(transformations.TRANSFORMATIONS)
    stock=base.STATE['embedding'].embed_to_file

    def embed_without_selected_rules(source,destination):
        transformations.TRANSFORMATIONS.clear()
        transformations.TRANSFORMATIONS.update({k:v for k,v in catalogue.items() if k not in OMIT})
        try:
            return stock(source,destination)
        finally:
            transformations.TRANSFORMATIONS.clear()
            transformations.TRANSFORMATIONS.update(catalogue)

    base.STATE['embedding'].embed_to_file=embed_without_selected_rules


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--upstream',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=2)
    args=p.parse_args()
    artifact,upstream,out=map(Path.resolve,(args.artifact,args.upstream,args.output))
    if out.exists():raise ValueError('Output must be new')
    tasks=base.load_tasks(artifact)
    out.mkdir(parents=True);(out/'sources').mkdir();(out/'records').mkdir()
    protocol={'status':'FIXED_BEFORE_EXECUTION','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'population':'All 164 HumanEval and 427 sanitized MBPP canonical-reference programs; identical original suites.',
              'source':'https://github.com/niccap/crest',
              'upstream_commit':subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip(),
              'embedding_intervention':{'omitted_rule_ids':list(OMIT),'remaining_rules':45,
                                       'selection':'Post-observation causal diagnostics of all 15 full-corpus stock failures.',
                                       'scope':'Catalogue ablation, not a proof of semantic preservation or a proposed universally safe repair.'},
              'detector':'Unchanged complete 49-rule feature extractor and all three released classifiers at their own unchanged upstream thresholds.',
              'source_files':{'run_crest_ablation.py':base.digest(Path(__file__)),'run_crest_study.py':base.digest(Path(base.__file__))},
              'source_policy':'Exact benchmark programs, no data or candidate filtering.',
              'native_policy':'Fresh unchanged original suite for every original and emitted source; retain missing emissions and unavailable evidence.',
              'workers':args.workers,'timing_claim':'No speed comparison; parallel run elapsed times are execution metadata.',
              'environment':{'python':sys.version,'platform':platform.platform(),
                             'dependencies':{name:importlib.metadata.version(name) for name in ['libcst','autopep8','chardet','numpy','scipy','scikit-learn','joblib']}}}
    base.write(out/'protocol.json',protocol);base.write(out/'tasks.json',tasks)
    results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,initializer=initialize,
                                                 initargs=(str(upstream),str(artifact),str(out))) as pool:
        futures={pool.submit(base.process,task):task for task in tasks}
        with (out/'completed.jsonl').open('w') as stream:
            for future in concurrent.futures.as_completed(futures):
                row=future.result();results.append(row)
                stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
                print(json.dumps({'completed':len(results),'total':len(tasks),'dataset':row['dataset'],
                                  'task_id':row['task_id'],'validity':row['validity'],'rf':row['classifiers']['rf']}),flush=True)
    results.sort(key=lambda r:(r['dataset']!='HumanEval',r['dataset_index']))
    base.write(out/'results.json',results)
    base.write(out/'summary.json',{'status':'COMPLETE','rows':len(results),'summaries':base.summarize(results)})
    print(json.dumps({'status':'COMPLETE','rows':len(results)}))


if __name__=='__main__':main()
