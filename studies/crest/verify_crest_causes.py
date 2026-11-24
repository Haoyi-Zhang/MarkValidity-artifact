#!/usr/bin/env python3
"""Receive all causal native observations without generating or executing code."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from verify_crest_study import receive_native


def require(condition,reason):
    if not condition:raise ValueError(reason)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();root=args.evidence;study=root/'accepted/causes'
    summary=json.loads((study/'summary.json').read_text())
    key=lambda r:(r['dataset'],str(r['task_id']))
    tasks={key(t):t for t in json.loads((root/'accepted/reference/tasks.json').read_text())}
    references={key(r):r for r in json.loads((root/'accepted/reference/results.json').read_text())}
    expected={k for k,r in references.items() if r['validity'] is False}
    require(len(summary['results'])==len(expected)==15 and {key(r) for r in summary['results']}==expected,
            'causal study omitted or added a canonical failure')
    previous=json.loads((root/'provenance/causal-generation/summary.json').read_text())
    protocol=json.loads((study/'protocol.json').read_text())
    require(hashlib.sha256((root/'provenance/causal-generation/summary.json').read_bytes()).hexdigest()==
            protocol['generation_summary_sha256'],'original causal generation record changed')
    earlier={key(r):r for r in previous['results']}
    observed=Counter();rules=Counter();count=0
    for case in summary['results']:
        identity=key(case);task=tasks[identity];reference=references[identity]
        require(case['implicated_rule']==earlier[identity]['implicated_rule'],'intervention choice changed')
        require(case['implicated_rule']==protocol['selection']['mapping'][str(case['task_id'])],
                'intervention differs from the declared post-diagnosis choice')
        rules[case['implicated_rule']]+=1
        old_interventions={r['intervention']:r for r in earlier[identity]['interventions']}
        require({r['intervention'] for r in case['interventions']}=={'full','omit','only'} and
                len(case['interventions'])==3,'incomplete intervention triplet')
        for intervention in case['interventions']:
            name=intervention['intervention'];receipt=intervention['native']
            source=(study/intervention['candidate_source']).read_bytes().decode('utf-8')
            request=({'source':source,'test':task['test'],'entry_point':task['entry_point']} if 'test' in task else
                     {'source':source,'test_imports':task['test_imports'],'test_list':task['test_list']})
            require(receipt['execution_request']==request,'causal request/source/original-contract mismatch')
            require(receipt['observer_file']==reference['reference_native']['observer_file'] and
                    receipt['observer_source_sha256']==hashlib.sha256((args.artifact/receipt['observer_file']).read_bytes()).hexdigest() and
                    receipt['execution_environment']==reference['reference_native']['execution_environment'],
                    'causal observer or execution environment differs from original contract')
            label=receive_native(receipt,task)
            require(label is receipt['label'] and label is (name=='omit'),
                    'causal source does not exhibit the claimed actual native outcome')
            require(intervention['candidate_source']==old_interventions[name]['candidate_source'] and
                    intervention['detector']==old_interventions[name]['detector'],
                    'causal generation or detector record changed during native replay')
            if name=='full':
                require(source.encode('utf-8')==(root/'accepted/reference'/reference['candidate_source']).read_bytes(),
                        'full-catalogue intervention does not reproduce the original candidate bytes')
            observed[name]+=1;count+=1
    require(count==summary['fresh_native_suites']==45 and
            summary['full_failures']==observed['full'] and summary['omission_passes']==observed['omit'] and
            summary['single_rule_failures']==observed['only'] and summary['all_default_emissions_identical'] is True,
            'causal aggregate differs from received raw outcomes')
    result={'status':'PASS','canonical_failures':len(expected),'native_request_observation_bindings':count,
            'full_catalogue_failures':observed['full'],'omission_passes':observed['omit'],
            'single_rule_failures':observed['only'],'implicated_rule_counts':dict(rules),
            'original_full_candidates_byte_equal':True,'native_program_executions':0,
            'scope':'Independent outcome-envelope parsing and exact source/original-contract/observer/environment binding for every causal intervention. Detector fields are retained generation evidence; this receiver makes no additional probability-recomputation claim.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
