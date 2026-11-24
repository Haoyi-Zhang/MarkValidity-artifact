#!/usr/bin/env python3
"""Re-execute every accepted source/contract with explicit submitted requests.

This closes the per-observation request binding. Generation and detector bytes
are retained; every behavioral result below is a new native subprocess result.
"""
import argparse
import concurrent.futures
import datetime
import json
from pathlib import Path
import shutil
import sys

import run_crest_study as base

STATE={}


def initialize(artifact,inputs,output):
    artifact=Path(artifact)
    base.STATE['artifact']=artifact
    sys.path.insert(0,str(artifact/'external-studies/sew_natural/comparison_costs'))
    import admission
    base.STATE['admission']=admission
    STATE.update(inputs={k:Path(v) for k,v in inputs.items()},output=Path(output))


def process(job):
    study,task,previous=job
    origin,out=STATE['inputs'][study],STATE['output']/study
    row={k:v for k,v in previous.items() if k not in
         {'reference_native','candidate_native','qualified_reference','validity','classifiers','observed_seconds'}}
    source=(origin/row['reference_source']).read_text()
    if source!=task['source']:raise ValueError('Source and task differ')
    (out/row['reference_source']).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(origin/row['reference_source'],out/row['reference_source'])
    routed=dict(task,dataset='HumanEval') if 'test' in task else task
    context=task.get('context_prompt','')
    row['reference_native']=base.native(routed,context+source)
    if 'candidate_source' in row:
        candidate=(origin/row['candidate_source']).read_text()
        shutil.copy2(origin/row['candidate_source'],out/row['candidate_source'])
        row['candidate_native']=base.native(routed,context+candidate)
    row['qualified_reference']=row['reference_native']['label'] is True
    row['validity']=row.get('candidate_native',{}).get('label') if row['qualified_reference'] else None
    row['classifiers']={}
    for model in base.MODELS:
        d=row.get('candidate_detector',{}).get('classifiers',{}).get(model,{}).get('detected')
        v=row['validity']
        j=False if v is False or d is False else (True if v is True and d is True else None)
        row['classifiers'][model]={'detected':d,'joint':j}
    # E is a directly observed pipeline event. Completed deterministic rejection
    # gives no output; program validity/detection remain N/A rather than false.
    if row['embedding']['status']=='completed' and 'candidate_source' in row:
        row['emission']='emitted'
    elif row['embedding']['status']=='error' and row['embedding'].get('error','').startswith('Error:'):
        row['emission']='rejected'
    else:
        row['emission']='unavailable'
    row['reexecution_comparison']={
        'reference_label_equal':row['reference_native']['label']==previous['reference_native']['label'],
        'candidate_label_equal':row.get('candidate_native',{}).get('label')==previous.get('candidate_native',{}).get('label')}
    stem=task['dataset'].lower()+'-'+str(task['task_id']).replace('/','-')
    base.write(out/'records'/(stem+'.json'),row)
    return study,row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--study',action='append',required=True,help='name=directory')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    out=args.output.resolve()
    if out.exists():raise ValueError('Output must be new')
    inputs={name:str(Path(path).resolve()) for name,path in (s.split('=',1) for s in args.study)}
    out.mkdir(parents=True)
    jobs=[];completed={name:[] for name in inputs};streams={}
    for name,folder in inputs.items():
        origin=Path(folder);target=out/name;target.mkdir();(target/'sources').mkdir();(target/'records').mkdir()
        tasks=json.loads((origin/'tasks.json').read_text())
        previous=json.loads((origin/'results.json').read_text())
        records={(r['dataset'],str(r['task_id'])):r for r in previous}
        if len(records)!=len(tasks):raise ValueError('Task population mismatch')
        base.write(target/'tasks.json',tasks)
        protocol={'status':'FIXED_BEFORE_EXECUTION','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'study':name,'generation_origin':origin.name,
                  'generation_results_sha256':base.digest(origin/'results.json'),
                  'input_task_table_sha256':base.digest(origin/'tasks.json'),
                  'producer_files':{'bind_fresh_native_evidence.py':base.digest(Path(__file__)),
                                    'run_crest_study.py':base.digest(Path(base.__file__))},
                  'native_contract':'Every receipt retains the exact request submitted to its fresh worker, worker-source identity, and execution environment. Generated completion requests use exact official prompt context; canonical benchmarks use their original native contract.',
                  'emission_policy':'Completed deterministic upstream rejection has known E=0 and zero operational output yield. Program V and detector D remain N/A. Interrupted/unavailable emission remains unknown.',
                  'historical_native_labels_used_for_new_decisions':False,
                  'comparison_to_earlier_measurement':'Earlier labels are compared only after fresh execution, solely to detect disagreements; they never determine a new label.',
                  'workers':args.workers,'timing_claim':'Correctness and provenance validation only; not a speed comparison.'}
        base.write(target/'protocol.json',protocol)
        streams[name]=(target/'completed.jsonl').open('w')
        for task in tasks:jobs.append((name,task,records[(task['dataset'],str(task['task_id']))]))
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,initializer=initialize,
                                                    initargs=(str(args.artifact.resolve()),inputs,str(out))) as pool:
            futures=[pool.submit(process,job) for job in jobs]
            for number,future in enumerate(concurrent.futures.as_completed(futures),1):
                name,row=future.result();completed[name].append(row)
                streams[name].write(json.dumps(row,ensure_ascii=False)+'\n');streams[name].flush()
                if number%100==0:print(json.dumps({'completed':number,'total':len(jobs)}),flush=True)
    finally:
        for stream in streams.values():stream.close()
    summary={}
    for name,rows in completed.items():
        rows.sort(key=lambda r:(r['dataset']!='HumanEval',r['dataset_index']))
        base.write(out/name/'results.json',rows)
        summary[name]={'rows':len(rows),'native_suites':sum(1+('candidate_native'in r) for r in rows),
                       'different_reference_labels':sum(not r['reexecution_comparison']['reference_label_equal'] for r in rows),
                       'different_candidate_labels':sum(not r['reexecution_comparison']['candidate_label_equal'] for r in rows)}
    base.write(out/'execution-summary.json',{'status':'COMPLETE','studies':summary})
    print(json.dumps({'status':'COMPLETE','studies':summary}))


if __name__=='__main__':main()
