#!/usr/bin/env python3
"""Fresh official-context execution of already emitted published completions.

Generation, detector feature extraction and classifier decisions are reused as
source-bound evidence. All behavioral labels are freshly measured after adding
the exact mxeval prompt as execution context, as the official executor does.
The earlier standalone execution records are not admitted into this study.
"""
import argparse
import concurrent.futures
import datetime
import json
from pathlib import Path
import shutil

import run_crest_study as base

STATE={}


def initialize(artifact,previous,output):
    base.STATE['artifact']=Path(artifact)
    import sys
    sys.path.insert(0,str(Path(artifact)/'external-studies/sew_natural/comparison_costs'))
    import admission
    base.STATE['admission']=admission
    STATE.update(previous=Path(previous),output=Path(output))


def process(job):
    task,previous=job
    row={k:v for k,v in previous.items() if k not in
         {'reference_native','candidate_native','qualified_reference','validity','classifiers','observed_seconds'}}
    source=(STATE['previous']/row['reference_source']).read_text()
    if source!=task['source']:raise ValueError('Published input source changed')
    ref_dest=STATE['output']/row['reference_source'];ref_dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(STATE['previous']/row['reference_source'],ref_dest)
    routed=dict(task,dataset='HumanEval')
    row['reference_native']=base.native(routed,task['context_prompt']+source)
    if 'candidate_source' in row:
        candidate=(STATE['previous']/row['candidate_source']).read_text()
        shutil.copy2(STATE['previous']/row['candidate_source'],STATE['output']/row['candidate_source'])
        row['candidate_native']=base.native(routed,task['context_prompt']+candidate)
    row['qualified_reference']=row['reference_native']['label'] is True
    row['validity']=row.get('candidate_native',{}).get('label') if row['qualified_reference'] else None
    row['classifiers']={}
    for model in base.MODELS:
        d=row.get('candidate_detector',{}).get('classifiers',{}).get(model,{}).get('detected')
        v=row['validity']
        j=False if v is False or d is False else (True if v is True and d is True else None)
        row['classifiers'][model]={'detected':d,'joint':j}
    stem=task['dataset'].lower()+'-'+str(task['task_id']).replace('/','-')
    base.write(STATE['output']/'records'/(stem+'.json'),row)
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--humaneval-contracts',type=Path,required=True)
    p.add_argument('--mbpp-contracts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    previous,out,artifact=map(Path.resolve,(args.previous,args.output,args.artifact))
    if out.exists():raise ValueError('Output must be new')
    original=json.loads((previous/'results.json').read_text())
    tasks=json.loads((previous/'tasks.json').read_text())
    by_key={(r['dataset'],r['task_id']):r for r in original}
    contracts={}
    for dataset,file in [('HumanEval',args.humaneval_contracts),('MBPP',args.mbpp_contracts)]:
        for line in file.read_text().splitlines():
            if line.strip():
                item=json.loads(line);contracts[(dataset,item['task_id'])]=item
    for task in tasks:
        contract=contracts[(task['dataset'],task['task_id'])]
        if task['test']!=contract['test'] or task['entry_point']!=contract['entry_point']:
            raise ValueError('Task mapping, test body or entry point changed')
        task['context_prompt']=contract['prompt']
    out.mkdir(parents=True);(out/'sources').mkdir();(out/'records').mkdir()
    protocol={'status':'FIXED_BEFORE_EXECUTION','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'cohort':json.loads((previous/'protocol.json').read_text())['cohort'],
              'generation_source':str(previous.name),'generation_protocol_sha256':base.digest(previous/'protocol.json'),
              'generation_results_sha256':base.digest(previous/'results.json'),
              'behavioral_contract':'Exact official mxeval prompt + exact published source or emitted candidate, then exact check(candidate) body and entry point. The input source supplied to CREST remains the exact stored file.',
              'earlier_standalone_observation_admission':False,
              'qualification':'Every input tested first; candidate preservation only for passing originals. All attempt records retained.',
              'contract_files':{'HumanEval':base.digest(args.humaneval_contracts),'MBPP':base.digest(args.mbpp_contracts)},
              'producer_files':{'execute_crest_in_prompt_context.py':base.digest(Path(__file__)),'run_crest_study.py':base.digest(Path(base.__file__))},
              'workers':args.workers,'timing_claim':'Correctness-only subprocess evaluation; no speed comparison.'}
    base.write(out/'protocol.json',protocol);base.write(out/'tasks.json',tasks)
    rows=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,initializer=initialize,
                                                 initargs=(str(artifact),str(previous),str(out))) as pool:
        futures=[pool.submit(process,(task,by_key[(task['dataset'],task['task_id'])])) for task in tasks]
        with (out/'completed.jsonl').open('w') as stream:
            for future in concurrent.futures.as_completed(futures):
                row=future.result();rows.append(row)
                stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
                if len(rows)%50==0:print(json.dumps({'completed':len(rows),'total':len(tasks)}),flush=True)
    rows.sort(key=lambda r:(r['dataset']!='HumanEval',r['dataset_index']))
    base.write(out/'results.json',rows)
    base.write(out/'summary.json',{'status':'COMPLETE','cohort':protocol['cohort'],'rows':len(rows),'summaries':base.summarize(rows)})
    print(json.dumps({'status':'COMPLETE','cohort':protocol['cohort'],'rows':len(rows)}))


if __name__=='__main__':main()
