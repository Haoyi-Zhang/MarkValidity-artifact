#!/usr/bin/env python3
"""Independently bind original inputs, official contracts and submitted requests."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(raw):return raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
def require(condition,reason):
    if not condition:raise ValueError(reason)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True)
    p.add_argument('--kind',choices=['reference','catalogue','gpt4o','qwen'],required=True)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--upstream',type=Path,help='Acquired repository root; defaults to inputs/upstream or inputs/crest')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    tasks=json.loads((args.study/'tasks.json').read_text())
    rows=json.loads((args.study/'results.json').read_text())
    protocol=json.loads((args.study/'protocol.json').read_text())
    direct_assertions=protocol.get('execution_contract')=='official_original_assertion_suite'
    isolated_assertions=protocol.get('execution_contract')=='official_original_assertions_isolated_namespaces'
    assertion_contract=direct_assertions or isolated_assertions
    if assertion_contract:
        require(digest(args.inputs/protocol['official_assembly_source'])==protocol['official_assembly_source_sha256'],
                'official check-program assembly source changed')
        require(protocol['typed_evidence_used_for_decisions'] is False,
                'typed observations must not determine direct-suite outcomes')
        typed=args.inputs/'contract-sensitivity/typed'/args.kind
        if not typed.exists():typed=args.inputs/'validated'/args.kind
        require(digest(typed/'results.json')==protocol['typed_evidence_results_sha256'],
                'retained preceding typed observations changed')
    def generation_folder(name):
        candidate=args.inputs/name
        return candidate if candidate.exists() else args.inputs/'provenance/generation-records'/name
    origin=generation_folder(protocol['generation_origin'])
    require(digest(origin/'results.json')==protocol['generation_results_sha256'],
            'generation record bytes differ from declared input')
    require(digest(origin/'tasks.json')==protocol['input_task_table_sha256'] and
            digest(args.study/'tasks.json')==protocol['input_task_table_sha256'],
            'task table changed since execution was fixed')
    for file,identity in protocol['producer_files'].items():
        require(digest(args.inputs/file)==identity,'native producer source identity changed')
    generated={(r['dataset'],str(r['task_id'])):r for r in json.loads((origin/'results.json').read_text())}
    origin_protocol=json.loads((origin/'protocol.json').read_text())
    acquisition=json.loads((generation_folder('full-study')/'protocol.json').read_text())
    upstream=args.upstream or (args.inputs/'upstream' if (args.inputs/'upstream').exists() else args.inputs/'crest')
    require(acquisition['source']=='https://github.com/niccap/crest', 'unexpected acquired implementation')
    for file,identity in acquisition['upstream_files'].items():
        require(digest(upstream/file)==identity,'upstream implementation/model/threshold identity changed')
    producer_alias={'run_crest_study.py':'unbound_study_producer.py',
                    'run_crest_generated.py':'preliminary_generated_producer.py'}
    if args.kind in ('gpt4o','qwen'):
        earlier=generation_folder(origin_protocol['generation_source'])
        require(digest(earlier/'protocol.json')==origin_protocol['generation_protocol_sha256'] and
                digest(earlier/'results.json')==origin_protocol['generation_results_sha256'],
                'published generation record chain changed')
        generation_protocol=json.loads((earlier/'protocol.json').read_text())
        original_generated={(r['dataset'],str(r['task_id'])):r for r in
                            json.loads((earlier/'results.json').read_text())}
        require(set(original_generated)==set(generated),'context stage changed the original generation population')
        for key,context_record in generated.items():
            original_record=original_generated[key]
            for field in ('embedding','reference_detector','candidate_detector','reference_source','candidate_source','source_changed'):
                require(context_record.get(field)==original_record.get(field),
                        'context stage changed generation/detection evidence')
            for side in ('reference','candidate'):
                if side+'_source' in context_record:
                    require((origin/context_record[side+'_source']).read_bytes()==
                            (earlier/original_record[side+'_source']).read_bytes(),
                            'context source bytes differ from original generation source')
        require(digest(args.inputs/'published-dataset.rar')==generation_protocol['published_archive_sha256'],
                'published program archive changed')
        for dataset,file in [('HumanEval','mxeval-humaneval.jsonl'),('MBPP','mxeval-mbpp.jsonl')]:
            require(digest(args.inputs/file)==generation_protocol['contract_files'][dataset]==origin_protocol['contract_files'][dataset],
                    'official generated-task contract bytes changed')
        for file,identity in generation_protocol['producer_files'].items():
            require(digest(args.inputs/producer_alias.get(file,file))==identity,
                    'original generation producer snapshot changed')
    else:
        generation_protocol=origin_protocol
    require(generation_protocol['upstream_commit']==acquisition['upstream_commit'],
            'generation uses a different upstream acquisition')
    amendment=None
    amended_expected={'gpt4o':'HumanEval/150','qwen':'HumanEval/32'}
    if (args.study/'contract-amendment.json').exists():
        amendment=json.loads((args.study/'contract-amendment.json').read_text())
        require(amendment['cohort']==args.kind and amendment['task_id']==amended_expected.get(args.kind),
                'unexpected per-task execution amendment')
        for file_key,identity_key in [('dependency_protocol','dependency_protocol_sha256'),
                                      ('receipts_file','receipts_sha256'),
                                      ('observer_protocol','observer_protocol_sha256')]:
            if amendment[file_key] is not None:
                require(digest(args.inputs/amendment[file_key])==amendment[identity_key],
                        'amendment source record changed')
        require(digest(args.inputs/'dependency-contracts/import-incidence.json')==amendment['import_incidence_sha256'],
                'declared import population changed')
        dependency_protocol=json.loads((args.inputs/amendment['dependency_protocol']).read_text())
        require(dependency_protocol['input_scan_rows']==2276 and
                {(r['cohort'],r['task_id'],tuple(r['external'])) for r in dependency_protocol['contracts']}==
                {('gpt4o','HumanEval/150',('sympy',)),('qwen','HumanEval/32',('numpy',))},
                'dependency amendment does not cover the complete declared import selection')
        final_receipts=json.loads((args.inputs/amendment['receipts_file']).read_text())
        amended_receipts={r['side']:r['native'] for r in final_receipts if r['cohort']==args.kind}
        require(set(amended_receipts)=={'reference','candidate'},'incomplete amended task pair')
    taskmap={(t['dataset'],str(t['task_id'])):t for t in tasks}
    require(len(taskmap)==len(tasks)==len(rows),'incomplete/duplicated task population')
    originals={};normalization_count=0
    if args.kind in ('reference','catalogue'):
        source=args.artifact/'external-studies/sew_natural'
        with gzip.open(source/'data/HumanEval.jsonl.gz','rt') as stream:
            for line in stream:
                if line.strip():
                    item=json.loads(line)
                    originals[('HumanEval',item['task_id'])]={'source':item['prompt']+item['canonical_solution'],
                                                            'test':item['test'],'entry_point':item['entry_point']}
        for item in json.loads((source/'mbpp/sanitized-mbpp.json').read_text()):
            originals[('MBPP',str(item['task_id']))]={'source':item['code'],'test_imports':item['test_imports'],
                                                    'test_list':item['test_list']}
    else:
        import libarchive
        folders={'gpt4o':('HE_4o_G','MBPP_4o_G'),'qwen':('HE_Q_G','MBPP_Q_G')}[args.kind]
        contracts={}
        for dataset,file in [('HumanEval','mxeval-humaneval.jsonl'),('MBPP','mxeval-mbpp.jsonl')]:
            for line in (args.inputs/file).read_text().splitlines():
                if line.strip():
                    item=json.loads(line);contracts[(dataset,item['task_id'])]=item
        raw_sources={}
        prefixes=tuple('dataset/G/'+folder+'/' for folder in folders)
        with libarchive.file_reader(str(args.inputs/'published-dataset.rar')) as archive:
            for entry in archive:
                if entry.pathname.startswith(prefixes) and entry.pathname.endswith('.py'):
                    raw=b''.join(entry.get_blocks())
                    dataset='HumanEval' if entry.pathname.startswith(prefixes[0]) else 'MBPP'
                    task_id=re.sub(r'([a-zA-Z]+)[_\s-]?(\d+)',r'\1/\2',Path(entry.pathname).stem)
                    key=(dataset,task_id)
                    require(key not in raw_sources,'duplicate published program')
                    raw_sources[key]=(entry.pathname,raw)
        require(len(raw_sources)==1138 and set(raw_sources)==set(contracts),'missing/unmapped published input or official contract')
        for key,(name,raw) in raw_sources.items():
            text=normalized(raw);normalization_count+=raw!=text.encode('utf-8')
            item=contracts[key]
            originals[key]={'source':text,'test':item['test'],'entry_point':item['entry_point'],
                            'context_prompt':item['prompt']}
    require(set(taskmap)==set(originals),'study population does not equal complete declared input population')
    checked=0;observers={};environments={};rejections=0;submitted_sources=[]
    for row in rows:
        key=(row['dataset'],str(row['task_id']));task=taskmap[key];expected=originals[key]
        earlier=generated[key]
        for field in ('embedding','reference_detector','candidate_detector','reference_source','candidate_source','source_changed'):
            require(row.get(field)==earlier.get(field),'generation or detection changed during native replay')
        for side in ('reference','candidate'):
            if side+'_source' in row:
                require((args.study/row[side+'_source']).read_bytes()==(origin/earlier[side+'_source']).read_bytes(),
                        'current source bytes differ from retained generation source')
        for field,value in expected.items():require(task.get(field)==value,'input/contract changed: '+str(key)+' '+field)
        require((args.study/row['reference_source']).read_bytes()==task['source'].encode('utf-8'),'retained reference text differs from actual submitted text')
        if row['emission']=='rejected':
            require(row['embedding']['status']=='error' and
                    row['embedding'].get('error','').startswith('Error:') and
                    row['embedding']['error'].endswith(' is not a valid Python file.') and
                    'candidate_source' not in row and 'candidate_native' not in row and
                    'traceback' not in row['embedding'],
                    'only completed known precheck rejection without any candidate is terminal E=0')
            rejections+=1
        for side in ('reference','candidate'):
            if side+'_native' not in row:continue
            native=row[side+'_native'];file=args.study/row[side+'_source']
            context=task.get('context_prompt','')
            source=context+file.read_bytes().decode('utf-8')
            if 'test' in task:
                request={'source':source,'test':task['test'],'entry_point':task['entry_point']}
                observer='external-studies/sew_natural/scripts/humaneval/native_runner_v3.py'
            else:
                request={'source':source,'test_imports':task['test_imports'],'test_list':task['test_list']}
                observer='external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'
            amended=amendment is not None and str(row['task_id'])==amendment['task_id']
            observer_root=args.artifact
            if assertion_contract:
                observer='isolated_assertion_native_runner.py' if isolated_assertions else 'assertion_native_runner.py'
                observer_root=args.inputs
            if amended:
                require(native==amended_receipts[side],'current amended native receipt differs from fresh paired execution')
                require(row.get('execution_contract_amendment')=='contract-amendment.json',
                        'missing explicit per-task amendment declaration')
                observer=amendment['observer_file']
                if args.kind=='qwen':observer_root=args.inputs
            require(native.get('execution_request')==request,'native request does not match exact source plus complete contract')
            require(native.get('observer_file')==observer,'unexpected observer file')
            require(native.get('observer_source_sha256')==digest(observer_root/observer),'native observer identity changed')
            env=native.get('execution_environment')
            require(env and env['hash_seed']=='0' and env['optimization_disabled'] is True and
                    env['wall_timeout_seconds']==15 and env['cpu_seconds']==10 and env['address_space_bytes']==1073741824,
                    'unaccounted native execution settings')
            if amended:
                require(env==amendment['execution_environment'] and env['site_initialization']=='enabled' and
                        env['invocation_flags']==['-B'] and env['pythonpath_removed'] is True and
                        env['declared_dependencies']=={m:dependency_protocol['packages'][m] for m in
                                                      (['sympy'] if args.kind=='gpt4o' else ['numpy'])},
                        'undeclared amended dependency environment')
            if assertion_contract:
                require(env==protocol['environment'] and env['site_initialization']=='enabled' and
                        env['invocation_flags']==['-B'] and env['pythonpath_removed'] is True and
                        set(env['declared_dependencies'])=={'numpy','sympy'},
                        'direct assertion contract has an undeclared environment')
            observers[observer]=native['observer_source_sha256']
            environments[json.dumps(env,sort_keys=True)]=env
            checked+=1
        if 'candidate_native' in row:
            require(row['reference_native']['execution_environment']==row['candidate_native']['execution_environment'] and
                    row['reference_native']['observer_source_sha256']==row['candidate_native']['observer_source_sha256'],
                    'reference and candidate do not share the same per-task observer and environment')
    require(len(environments)==(2 if amendment else 1),'undeclared execution environment')
    result={'status':'PASS','study':args.kind,'input_rows':len(rows),'archive_or_benchmark_source_bindings':len(tasks),
            'official_contract_bindings':len(tasks),'native_request_bindings':checked,
            'decoded_input_files_with_line_ending_normalization':normalization_count,
            'input_text_policy':'UTF-8 with Python universal-newline decoding. Archived bytes and actual submitted text are verified as separate objects; no token-level edits.',
            'verified_completed_emission_rejections':rejections,'observers':observers,
            'execution_environments':list(environments.values()),
            'paired_execution_contracts_verified':True,
            'original_assertions_without_value_instrumentation':assertion_contract,
            'literal_official_executor_assembly':direct_assertions,
            'namespace_bindings_separated':isolated_assertions,
            'declared_dependency_amendments':1 if amendment else 0,
            'upstream_core_model_threshold_bindings':len(acquisition['upstream_files']),
            'feature_reextraction_scope':'Separate official CLI checks cover selected input/candidate pairs; this receiver does not claim all-source feature re-extraction.',
            'scope':'Actual request/source/contract/observer/environment identity, source decoding, complete declared input mapping, and valid terminal no-output events. Numerical outcomes and classifier scores have a separate receiver.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('observers','execution_environments')}))


if __name__=='__main__':main()
