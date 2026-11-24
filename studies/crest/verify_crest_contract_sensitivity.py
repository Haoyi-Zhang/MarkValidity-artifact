#!/usr/bin/env python3
"""Independently receive the full literal/separate-namespace difference set."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def require(condition,reason):
    if not condition:raise ValueError(reason)


def native_label(receipt):
    if receipt['returncode']!=0 or receipt['interruption']:return None
    obj=json.loads(receipt['stdout'])
    require(isinstance(obj,dict) and type(obj['check_finished']) is bool,'invalid native suite envelope')
    require(obj.get('schema') in {'crest-original-assertion-suite','crest-isolated-original-assertions'},
            'unexpected assertion observer schema')
    if obj['status']=='passed':
        require(obj['check_finished'] and obj['error'] is None,'incomplete passing check')
        return True
    if obj['status']=='failed':
        phases=({'compile_check_program','execute_check_program'} if obj['schema']=='crest-original-assertion-suite' else
                {'compile_source','initialize_source','resolve_entry_point','original_suite'})
        require(not obj['check_finished'] and not obj['error'].get('reason') and
                obj['error']['phase'] in phases and obj['error']['type'] not in
                {'builtins.MemoryError','builtins.KeyboardInterrupt'},'not a witnessed program failure')
        return False
    require(obj['status']=='unavailable' and not obj['check_finished'],'unknown native state')
    return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.evidence
    expected=json.loads((root/'contract-sensitivity/summary.json').read_text())
    changes,collisions=[],[]
    count=0
    for cohort in ('gpt4o','qwen'):
        old,new=root/'contract-sensitivity/literal'/cohort,root/'accepted'/cohort
        load=lambda folder:{(r['dataset'],str(r['task_id'])):r for r in json.loads((folder/'results.json').read_text())}
        literal,primary=load(old),load(new)
        tasks={t['task_id']:t for t in json.loads((new/'tasks.json').read_text())}
        require(len(tasks)==len(literal)==len(primary)==1138 and set(literal)==set(primary),'population changed')
        require(json.loads((old/'tasks.json').read_text())==json.loads((new/'tasks.json').read_text()),
                'original task/test table differs')
        for key,row in primary.items():
            before=literal[key];task=tasks[row['task_id']]
            item={'cohort':cohort,'dataset':row['dataset'],'task_id':row['task_id'],
                  'entry_point':task['entry_point'],'labels':{}}
            for field in ('embedding','reference_detector','candidate_detector','reference_source','candidate_source','emission'):
                require(row.get(field)==before.get(field),'generation or detection differs')
            for side in ('reference','candidate'):
                if side+'_native' not in row:
                    require(side+'_native' not in before,'different emission availability')
                    continue
                a,b=before[side+'_native'],row[side+'_native']
                require(a['execution_request']==b['execution_request'] and a['execution_environment']==b['execution_environment'],
                        'program, original assertions or environment changed')
                require((old/before[side+'_source']).read_bytes()==(new/row[side+'_source']).read_bytes(),'source bytes changed')
                for receipt,filename in [(a,'assertion_native_runner.py'),(b,'isolated_assertion_native_runner.py')]:
                    require(receipt['observer_source_sha256']==hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                            'declared observer differs from executed source snapshot')
                x,y=native_label(a),native_label(b)
                require(x is a['label'] and y is b['label'],'native admission mismatch')
                item['labels'][side]={'literal':x,'separate_bindings':y};count+=1
            if any(x['literal']!=x['separate_bindings'] for x in item['labels'].values()):changes.append(item)
            definitions={n.name for n in ast.parse(task['test']).body if isinstance(n,ast.FunctionDef)}
            if task['entry_point'] in definitions:
                require(task['entry_point']=='check','unexpected test-entry binding collision')
                collisions.append(item)
    require(count==expected['source_contract_pairs_received']==4434,'incomplete receipt-pair coverage')
    require(changes==expected['full_difference_set'] and collisions==expected['all_check_collision_task_pairs'],
            'stored sensitivity report does not match complete native differences')
    canonical=json.loads((root/'contract-sensitivity/canonical-contract-controls.json').read_text())
    official={t['task_id']:t for t in map(json.loads,(root/'mxeval-mbpp.jsonl').read_text().splitlines())}
    for record in canonical['records']:
        task=official[record['task_id']]
        request={'source':task['prompt']+task['canonical_solution'],'test':task['test'],'entry_point':task['entry_point']}
        for method,label in [('literal',False),('separate',True)]:
            receipt=record['receipts'][method]
            require(receipt['execution_request']==request and native_label(receipt) is label,
                    'canonical-solution control does not support name-collision diagnosis')
    result={'status':'PASS','native_receipt_pairs_received':count,'input_pairs':2276,
            'changed_input_pairs':len(changes),'changed_native_labels':sum(
                sum(x['literal']!=x['separate_bindings'] for x in row['labels'].values()) for row in changes),
            'collision_task_pairs':len(collisions),'official_canonical_controls':len(canonical['records']),
            'outside_collision_differences':sum(row['entry_point']!='check' for row in changes)}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
