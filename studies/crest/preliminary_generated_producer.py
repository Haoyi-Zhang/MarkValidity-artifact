#!/usr/bin/env python3
"""Assess all released generated HumanEval/MBPP programs without source repair.

Repository filenames are converted to benchmark IDs exactly as in CREST's
prepare_data_for_passk.py. Published source bytes are not completed, cleaned,
filtered, or repaired. Complete mxeval contracts provide 164+974 task IDs.
"""
import argparse
import concurrent.futures
import datetime
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

import run_crest_study as base

NATIVE = base.native


def native_generated(task, source):
    # Both mxeval files expose check(candidate), so the same retained observer
    # invokes the exact supplied test body and declared entry point.
    routed = dict(task, dataset='HumanEval')
    return NATIVE(routed, source)


def initialize(upstream, artifact, output):
    base.initialize(upstream, artifact, output)
    base.native = native_generated


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--upstream',type=Path,required=True)
    p.add_argument('--programs',type=Path,required=True)
    p.add_argument('--humaneval-contracts',type=Path,required=True)
    p.add_argument('--mbpp-contracts',type=Path,required=True)
    p.add_argument('--cohort',choices=['gpt4o','qwen'],required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=2)
    args=p.parse_args()
    artifact,upstream,programs,out=map(Path.resolve,(args.artifact,args.upstream,args.programs,args.output))
    if out.exists():raise ValueError('Output must be new')
    cohorts={'gpt4o':('HE_4o_G','MBPP_4o_G'),'qwen':('HE_Q_G','MBPP_Q_G')}
    tasks=[]
    mapping=[]
    for dataset,folder,contract_file,n in zip(('HumanEval','MBPP'),cohorts[args.cohort],
                                             (args.humaneval_contracts,args.mbpp_contracts),(164,974)):
        contracts=[json.loads(line) for line in contract_file.read_text().splitlines() if line.strip()]
        by_id={c['task_id']:c for c in contracts}
        files=sorted((programs/'dataset/G'/folder).glob('*.py'),key=lambda f:int(re.findall(r'\d+',f.stem)[-1]))
        if len(files)!=n or len(by_id)!=n:raise ValueError('Incomplete released population or contract set')
        converted=set()
        for index,file in enumerate(files):
            task_id=re.sub(r'([a-zA-Z]+)[_\s-]?(\d+)',r'\1/\2',file.stem)
            if task_id not in by_id or task_id in converted:raise ValueError('Unmapped/duplicate source ID: '+task_id)
            converted.add(task_id)
            c=by_id[task_id]
            task={'dataset':dataset,'dataset_index':index,'task_id':task_id,
                  'source':file.read_text(),'test':c['test'],'entry_point':c['entry_point']}
            tasks.append(task)
            mapping.append({'cohort':args.cohort,'dataset':dataset,'task_id':task_id,
                            'published_path':str(file.relative_to(programs)),
                            'entry_point':c['entry_point'],'source_sha256':base.digest(file)})
        if converted!=set(by_id):raise ValueError('A benchmark contract has no published source')
    out.mkdir(parents=True)
    (out/'sources').mkdir();(out/'records').mkdir()
    protocol={'status':'FIXED_BEFORE_EXECUTION','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'cohort':args.cohort,'source':'https://github.com/niccap/crest',
              'upstream_commit':subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip(),
              'published_archive_sha256':base.digest(base.HERE/'published-dataset.rar'),
              'primary_classifier':'rf','additional_classifiers':['logreg_l1','logreg_l2'],
              'threshold_policy':'Unchanged released strictest-available threshold. No local fitting, calibration, or classifier selection.',
              'source_policy':'All released raw source files in both named cohort folders, exactly as stored. No completion, trimming, source repair, or syntax/output filtering.',
              'contract_policy':'Exact mxeval check(candidate) test body and entry point joined by the upstream filename-to-task-ID rule. 164 HumanEval and 974 MBPP contracts, no substitutions or missing mappings.',
              'qualification_policy':'Every original source is executed first. Candidate preservation is established only where that original source passes the same suite. Original and candidate pass/fail/unavailable outcomes also remain separately available for every attempt.',
              'population':mapping,
              'contract_files':{'HumanEval':base.digest(args.humaneval_contracts),'MBPP':base.digest(args.mbpp_contracts)},
              'producer_files':{'run_crest_generated.py':base.digest(Path(__file__)),'run_crest_study.py':base.digest(Path(base.__file__))},
              'timeouts_seconds':{'embedding':120,'detection_per_source':120,'native_suite':15},
              'native_cpu_seconds':10,'native_address_space_bytes':1073741824,
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
                                  'task_id':row['task_id'],'qualified':row['qualified_reference'],
                                  'validity':row['validity'],'rf':row['classifiers']['rf']}),flush=True)
    results.sort(key=lambda r:(r['dataset']!='HumanEval',r['dataset_index']))
    base.write(out/'results.json',results)
    summaries=base.summarize(results)
    for s in summaries:
        rows=[r for r in results if s['dataset']=='pooled' or r['dataset']==s['dataset']]
        s['input_failed']=sum(r['reference_native']['label'] is False for r in rows)
        s['input_unavailable']=sum(r['reference_native']['label'] is None for r in rows)
        s['candidate_suite_passed']=sum(r.get('candidate_native',{}).get('label') is True for r in rows)
        s['candidate_suite_failed']=sum(r.get('candidate_native',{}).get('label') is False for r in rows)
        s['candidate_suite_unavailable_or_not_emitted']=sum(r.get('candidate_native',{}).get('label') is None for r in rows)
        s['emitted_candidates']=sum('candidate_source' in r for r in rows)
        s['qualified_D']=sum(r['qualified_reference'] and r['classifiers'][s['classifier']]['detected'] is True for r in rows)
        s['unqualified_D']=sum(not r['qualified_reference'] and r['classifiers'][s['classifier']]['detected'] is True for r in rows)
    base.write(out/'summary.json',{'status':'COMPLETE','cohort':args.cohort,'rows':len(results),'summaries':summaries})
    print(json.dumps({'status':'COMPLETE','cohort':args.cohort,'rows':len(results)}))


if __name__=='__main__':main()
