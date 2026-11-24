#!/usr/bin/env python3
"""Counterfactual rule ablations for every observed canonical-reference failure.

These post-observation diagnostics identify failure mechanisms; they are not a
claim that globally disabling the selected rules is a generally correct repair.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile

import run_crest_study as base


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--upstream',type=Path,required=True)
    p.add_argument('--study',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    out=args.output.resolve()
    if out.exists():raise ValueError('Output must be new')
    out.mkdir(parents=True);(out/'sources').mkdir()
    base.initialize(str(args.upstream.resolve()),str(args.artifact.resolve()),str(out))
    import transformations
    full=dict(transformations.TRANSFORMATIONS)
    rows=json.loads((args.study/'results.json').read_text())
    tasks={(t['dataset'],str(t['task_id'])):t for t in json.loads((args.study/'tasks.json').read_text())}
    selected=[r for r in rows if r['validity'] is False]
    mapping={str(i):r for i,r in [(106,46),(126,24),(278,20),(414,38),(421,46),(422,24),(437,46),(630,46),(632,46),(791,46)]}
    for i in [10,79,119,140,160]:mapping['HumanEval/'+str(i)]=46
    if set(str(r['task_id']) for r in selected)!=set(mapping):raise ValueError('Unaccounted failure')
    base.write(out/'protocol.json',{'selection':'Every candidate contradicted by fresh original tests in the complete canonical-reference run.',
                                  'selection_timing':'Chosen after observing all original full-study results and source differences.',
                                  'interventions':['unchanged full catalogue','omit the implicated rule','apply only the implicated rule'],
                                  'mapping':mapping,'detector':'Always unchanged full catalogue and released RF model at its original threshold.',
                                  'execution':'Fresh source and original suite per intervention; no prior candidate labels reused.'})
    results=[]
    for original in selected:
        task=tasks[(original['dataset'],str(original['task_id']))]
        rule=mapping[str(task['task_id'])]
        stem=task['dataset'].lower()+'-'+str(task['task_id']).replace('/','-')
        case={'dataset':task['dataset'],'task_id':task['task_id'],'implicated_rule':rule,'interventions':[]}
        for intervention in ('full','omit','only'):
            catalogue=full if intervention=='full' else ({k:v for k,v in full.items() if k!=rule} if intervention=='omit' else {rule:full[rule]})
            transformations.TRANSFORMATIONS.clear();transformations.TRANSFORMATIONS.update(catalogue)
            log=io.StringIO()
            previous=Path.cwd()
            with tempfile.TemporaryDirectory(prefix='crest-causal-') as tmp:
                os.chdir(tmp)
                source=Path(tmp)/'source.py';candidate=Path(tmp)/'candidate.py'
                source.write_text(task['source'])
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    error=base.guarded(lambda:base.STATE['embedding'].embed_to_file(str(source),str(candidate)),120)
                if error or not candidate.is_file():raise ValueError('Ablation did not emit: '+str(error))
                candidate_text=candidate.read_text()
                rel='sources/'+stem+'-'+intervention+'.py';(out/rel).write_text(candidate_text)
                native=base.native(task,candidate_text)
                transformations.TRANSFORMATIONS.clear();transformations.TRANSFORMATIONS.update(full)
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    detection=base.detect(candidate)
                os.chdir(previous)
            observation={'intervention':intervention,'candidate_source':rel,'native':native,
                         'detector':detection,'upstream_log':log.getvalue()}
            if intervention=='full':
                observation['matches_original_emission_bytes']=candidate_text==(args.study/original['candidate_source']).read_text()
                if not observation['matches_original_emission_bytes']:raise ValueError('Default output changed')
            case['interventions'].append(observation)
        results.append(case)
        base.write(out/(stem+'.json'),case)
        print(json.dumps({'task':case['task_id'],'rule':rule,'validity':[x['native']['label'] for x in case['interventions']]}),flush=True)
    summary={'status':'COMPLETE','failures':len(results),'fresh_native_suites':3*len(results),
             'full_failures':sum(x['interventions'][0]['native']['label'] is False for x in results),
             'omission_passes':sum(x['interventions'][1]['native']['label'] is True for x in results),
             'single_rule_failures':sum(x['interventions'][2]['native']['label'] is False for x in results),
             'all_default_emissions_identical':all(x['interventions'][0]['matches_original_emission_bytes'] for x in results),
             'results':results}
    base.write(out/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}))


if __name__=='__main__':main()
