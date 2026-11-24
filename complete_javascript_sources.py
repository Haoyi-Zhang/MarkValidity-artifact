"""Execute every stored JavaScript source on its complete frozen input domain.

This is a trusted owned-code study, not an arbitrary-code sandbox. All candidate
bytes are retained in the source inventory. A narrow source-shape check excludes
ambient state and top-level code; it does not supply the behavioral label.
Every label requires fresh-module-per-input execution, and full typed output
vectors are retained with post-execution content-addressed deduplication.
Earlier partial-evidence results remain immutable and are compared explicitly.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'src'))
from covewm.tasks import TASK_BY_NAME, domain_cases

OBSERVATION_RULE = 'covewm-tagged-return-or-exception-type-and-message-canonical-json-v2'
INITIALIZATION_RULE = 'covewm-fresh-module-instance-per-input-v1'
SCHEMES = ('lexical', 'structural', 'hybrid')
WEIGHTS = {
    'balanced': {a: Fraction(1, 5) for a in ('rename','normalize','random_flip','strip','mixed')},
    'rename-heavy': {'rename': Fraction(54,100), 'random_flip': Fraction(24,100), 'strip': Fraction(22,100)},
    'structure-heavy': {'normalize': Fraction(54,100), 'random_flip': Fraction(24,100), 'strip': Fraction(22,100)},
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))

def digest(data):
    return hashlib.sha256(data.encode('utf-8') if isinstance(data,str) else data).hexdigest()

def json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')

def csv_write(path, rows):
    require(bool(rows), 'empty CSV')
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)

@contextmanager
def gztext(path, mode='w'):
    if mode == 'r':
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as handle:
            yield handle
    else:
        with Path(path).open('wb') as binary:
            with gzip.GzipFile(filename='', fileobj=binary, mode='wb', mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as handle:
                    yield handle

def reference_source(task):
    return TASK_BY_NAME[task].javascript_reference.replace('__CARRIERS__','').rstrip()+'\n'

def validate_owned_source(task, source):
    """Conservative execution-isolation gate for the saved diagnostic family.

    The complete trusted reference suffix is byte-identical. Prefix statements
    may declare fresh local constants or empty local control blocks only. There
    is no top-level code, object argument, global assignment or dynamic lookup
    introduced by this prefix. This is not reported as an equivalence proof.
    """
    require(task in TASK_BY_NAME and isinstance(source,str), 'unknown task/source')
    template = TASK_BY_NAME[task].javascript_reference
    require(template.count('__CARRIERS__') == 1, 'reference placeholder mismatch')
    head, tail = template.split('__CARRIERS__')
    tail = tail.rstrip()+'\n'
    require(source.startswith(head) and source.endswith(tail), 'source differs from frozen function body')
    block = source[len(head):len(source)-len(tail)]
    lines = block.splitlines()
    position, previous, sites = 0, -1, 0
    names = set(re.findall(r'\b[A-Za-z_$][\w$]*\b', head+tail))
    while position < len(lines):
        if lines[position] == '':
            position += 1; continue
        padding = re.fullmatch(r'  // format-only padding for site (\d{2})', lines[position])
        if padding:
            position += 1
            require(position < len(lines), 'padding without site')
        marker = re.fullmatch(r'  // WM_SITE (\d{2}) (LEXICAL|STRUCTURAL)', lines[position])
        require(marker is not None, 'unexpected prefix token')
        index, channel = int(marker[1]), marker[2]
        require(previous < index < 24, 'site order/range mismatch')
        require(not padding or padding[1] == marker[1], 'padding/site mismatch')
        position += 1
        require(position < len(lines), 'missing local statement')
        statement = lines[position]
        if channel == 'LEXICAL':
            allowed = [f'wm_bit_{index:02d}', f'wmBit{index:02d}']
            name = next((name for name in allowed if statement == f'  const {name} = 0;'), None)
            require(name is not None, 'unregistered lexical statement')
            require(name not in names, 'local name captures reference')
            names.add(name)
        else:
            loop_name = f'_wm_{index:02d}'
            require(statement in ('  if (false) {}', f'  for (const {loop_name} of []) {{}}'), 'unregistered structural statement')
            require(loop_name not in names, 'local loop name captures reference')
            names.add(loop_name)
        position += 1; previous = index; sites += 1
    return sites

def records(path):
    with gztext(path, 'r') as handle:
        return [json.loads(line) for line in handle]

def run_task(spec, output, timeout):
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='markvalidity-completion-') as directory:
        spec_path = Path(directory)/'spec.json'
        spec_path.write_text(canonical(spec), encoding='utf-8')
        stdout_path, stderr_path = Path(directory)/'observed.jsonl', Path(directory)/'stderr.txt'
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            completed = subprocess.run(['node',str(HERE/'js/source_completion_runner.js'),str(spec_path)],
                stdout=stdout, stderr=stderr, timeout=timeout, check=False)
        require(completed.returncode == 0, f"Node failed for {spec['task']}: "+stderr_path.read_text()[-2000:])
        values = [json.loads(line) for line in stdout_path.read_text().splitlines()]
        require(values[0]['type']=='start' and values[-1]['type']=='finish', 'incomplete native stream')
        require(values[0]['spec_sha256']==digest(spec_path.read_bytes()), 'worker spec mismatch')
        with gztext(output/'raw'/f"{spec['task']}.jsonl.gz") as handle:
            handle.write(stdout_path.read_text())
        return dict(task=spec['task'], wall_seconds=round(time.monotonic()-started,6),
            command=['node','js/source_completion_runner.js','<canonical-temporary-spec.json>'],
            spec_sha256=digest(spec_path.read_bytes()), stderr=stderr_path.read_text(),
            worker_start=values[0],worker_finish=values[-1])

def generate_summaries(out, evidence, retained):
    registration = json.loads((out/'registration.json').read_text())
    labels, controls, references, nominal = {}, [], {}, {}
    for task in registration['tasks']:
        stream = records(out/'raw'/f'{task}.jsonl.gz')
        for record in stream:
            if record['type']=='nominal_program': nominal[(task,record['id'])]=record
            if record['type'] != 'program': continue
            if record['role']=='reference': references[task]=record
            elif record['role']=='candidate':
                key=(task,record['source_sha256']); require(key not in labels, 'duplicate source result')
                labels[key]=record
            elif record['role']=='mutant': controls.append(record)
    label_rows=[]
    for key, value in sorted(labels.items()):
        label_rows.append({field:value[field] for field in ('task','source_sha256','reference_sha256','domain_sha256',
            'validity','completed_cases','factory_initializations','observation_hash','legacy_observation_hash',
            'return_observations','exception_observations','mismatch_count','first_mismatch_index','elapsed_ms')})
    csv_write(out/'source_labels.csv',label_rows)
    control_rows=[]
    for r in controls:
        row={field:r[field] for field in ('task','id','source_sha256','validity','completed_cases',
            'observation_hash','legacy_observation_hash','mismatch_count','first_mismatch_index')}
        nr=nominal[(r['task'],r['id'])]
        row.update(nominal_cases=nr['completed_cases'],nominal_equal=nr['nominal_equal'],nominal_observation_hash=nr['observation_hash'])
        control_rows.append(row)
    csv_write(out/'mutant_controls.csv',control_rows)
    all_rows=[]
    with gztext(evidence/'rows.csv.gz','r') as handle:
        for row in csv.DictReader(handle):
            if row['task'] not in registration['tasks']: continue
            if row['language']=='javascript':
                observed=labels[(row['task'],row['source_sha256'])]
                v=int(observed['validity']=='supported'); basis='fresh-input-complete-native-execution'
                observation_hash=observed['observation_hash']
            else:
                require(row['validity_status']=='valid','Python proof label missing')
                v=1; basis='retained-restricted-erasure-proof';observation_hash=''
            d=int(row['detected'])
            all_rows.append(dict(task=row['task'],language=row['language'],scheme=row['scheme'],attack=row['attack'],
                severity=row['severity'],payload_index=row['payload_index'],source_sha256=row['source_sha256'],
                legacy_semantic_contract_id=row['semantic_contract_id'], prior_validity_status=row['validity_status'],
                prior_evidence_kind=row['evidence_kind'],validity=v,detected=d,joint=v*d,
                completed_behavioral_basis=basis,observation_hash=observation_hash))
    with gztext(out/'completed_rows.csv.gz') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(all_rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(all_rows)
    family=defaultdict(lambda:[0,0,0,0])
    for row in all_rows:
        acc=family[(row['language'],row['scheme'],row['attack'])]
        for i,x in enumerate([1,row['validity'],row['detected'],row['joint']]):acc[i]+=x
    family_rows=[]
    for key,(n,v,d,j) in sorted(family.items()):
        family_rows.append(dict(language=key[0],scheme=key[1],attack=key[2],configurations=n,validity_supported=v,
            detected=d,joint_count=j,joint_exact=str(Fraction(j,n)),joint=f'{j/n:.12f}'))
    csv_write(out/'family_scores.csv',family_rows)
    full_study=registration['complete_frozen_design']
    old_scores={}
    if full_study:
        with (evidence/'mixture_scores.csv').open() as handle:
            old_scores={(r['language'],r['mixture'],r['scheme']):r for r in csv.DictReader(handle)}
    score_rows=[];scores={}
    for language in ('python','javascript','combined'):
        for mixture, weights in WEIGHTS.items():
            for scheme in SCHEMES:
                langs=('python','javascript') if language=='combined' else (language,)
                value=sum((sum((weight*Fraction(family[(lang,scheme,attack)][3],family[(lang,scheme,attack)][0])
                    for attack,weight in weights.items()),Fraction()) for lang in langs),Fraction())/len(langs)
                scores[(language,mixture,scheme)]=value
                previous=old_scores.get((language,mixture,scheme))
                lower=previous['joint_lower_exact'] if previous else ''
                upper=previous['joint_upper_exact'] if previous else ''
                covered=(Fraction(lower)<=value<=Fraction(upper)) if previous else None
                score_rows.append(dict(language=language,mixture=mixture,scheme=scheme,joint_exact=str(value),
                    joint=f'{float(value):.12f}',earlier_lower_exact=lower,earlier_upper_exact=upper,
                    contained_in_earlier_interval=covered))
    csv_write(out/'mixture_scores.csv',score_rows)
    old_gaps={}
    if full_study:
        with (evidence/'pairwise_source_bounds.csv').open() as handle:
            old_gaps={(r['language'],r['mixture'],r['left'],r['right']):r for r in csv.DictReader(handle)}
    gap_rows=[]
    for language in ('python','javascript','combined'):
        for mixture in WEIGHTS:
            for i,left in enumerate(SCHEMES):
                for right in SCHEMES[i+1:]:
                    gap=scores[(language,mixture,left)]-scores[(language,mixture,right)]
                    old=old_gaps.get((language,mixture,left,right));lower=old['lower_exact'] if old else '';upper=old['upper_exact'] if old else ''
                    gap_rows.append(dict(language=language,mixture=mixture,left=left,right=right,gap_exact=str(gap),
                        gap=f'{float(gap):.12f}',preferred=left if gap>0 else right if gap<0 else '',
                        earlier_lower_exact=lower,earlier_upper_exact=upper,
                        contained_in_earlier_interval=Fraction(lower)<=gap<=Fraction(upper) if old else None))
    csv_write(out/'pairwise_gaps.csv',gap_rows)
    links=[]
    with (retained/'raw/semantic_audit.csv').open() as handle:
        for row in csv.DictReader(handle):
            if row['language']!='javascript' or row['task'] not in registration['tasks']:continue
            result=labels[(row['task'],row['source_sha256'])]
            links.append(dict(task=row['task'],scheme=row['scheme'],condition=row['condition'],source_sha256=row['source_sha256'],
                previous_bounded_equivalent=row['bounded_equivalent'],fresh_input_validity=result['validity'],
                fresh_observation_hash=result['observation_hash'],fresh_legacy_projection_hash=result['legacy_observation_hash'],
                same_domain_case_count=int(row['domain_cases'])==result['completed_cases']))
    csv_write(out/'previous_execution_links.csv',links)
    task_rows=[]
    for task in registration['tasks']:
        these=[r for (t,_),r in labels.items() if t==task]
        task_rows.append(dict(task=task,domain_cases=len(domain_cases(task)),distinct_sources=len(these),
            candidate_input_calls=sum(r['completed_cases'] for r in these),supported=sum(r['validity']=='supported' for r in these),
            contradicted=sum(r['validity']=='contradicted' for r in these),reference_observation_hash=references[task]['observation_hash'],
            reference_legacy_projection_hash=references[task]['legacy_observation_hash']))
    csv_write(out/'task_coverage.csv',task_rows)
    summary=dict(status='PASS',complete_frozen_design=full_study,quantity='joint yield E[validity AND detection]',
        source_selection='Every stored JavaScript source identity; no outcome-based source selection',
        observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,
        javascript_candidate_sources_executed=len(labels),javascript_candidate_input_calls=sum(r['completed_cases'] for r in labels.values()),
        javascript_reference_sources_executed=len(references),javascript_reference_input_calls=sum(r['completed_cases'] for r in references.values()),
        javascript_mutant_control_sources_executed=len(controls),javascript_mutant_control_input_calls=sum(r['completed_cases'] for r in controls),
        candidate_statuses=dict(Counter(r['validity'] for r in labels.values())),mutant_control_statuses=dict(Counter(r['validity'] for r in controls)),
        javascript_mutant_nominal_survivors=sum(r['nominal_equal'] for r in control_rows),
        nominal_input_calls=sum(r['completed_cases'] for r in nominal.values()),
        all_source_configurations=len(all_rows),javascript_configurations=sum(r['language']=='javascript' for r in all_rows),
        joint_count=sum(r['joint'] for r in all_rows),joint_exact=str(Fraction(sum(r['joint'] for r in all_rows),len(all_rows))),
        prior_unknown_javascript_configurations_completed=sum(r['language']=='javascript' and r['prior_validity_status']=='unknown' for r in all_rows),
        previous_executed_javascript_rows_linked=len(links),
        old_mixture_intervals_checked=len(score_rows) if full_study else 0,
        old_pairwise_intervals_checked=len(gap_rows) if full_study else 0,
        completed_scores_contained_in_prior_intervals=all(r['contained_in_earlier_interval'] for r in score_rows+gap_rows) if full_study else None,
        combined_mixtures=[r for r in score_rows if r['language']=='combined'],
        combined_winners={mixture:max(SCHEMES,key=lambda scheme:scores[('combined',mixture,scheme)]) for mixture in WEIGHTS},
        contract_relationship='The fresh-input tagged contract is explicit. Comparison with earlier intervals is empirical on these frozen sources; it does not assume arbitrary stateful programs retain legacy labels.',
        execution_scope='All JavaScript source identities executed. Python labels in the combined completion are the retained restricted proofs, not new executions in this command.',
        source_output_vector_storage='Full typed per-input observations retained once per identical vector only after direct execution and equality comparison; every source binds to its measured vector.')
    return summary

def run(evidence, retained, out, tasks=None, workers=2, timeout=1800):
    evidence,retained,out=map(lambda p:Path(p).resolve(),(evidence,retained,out))
    require(not out.exists(),'fresh output directory required')
    require(not out.is_relative_to(evidence) and not evidence.is_relative_to(out),'output overlaps input evidence')
    selected=sorted(tasks or TASK_BY_NAME)
    require(all(t in TASK_BY_NAME for t in selected) and len(set(selected))==len(selected),'unknown/duplicate task')
    source_rows=[r for r in records(evidence/'sources.jsonl.gz') if r['language']=='javascript' and r['task'] in selected]
    by_task=defaultdict(list);seen=set()
    for row in source_rows:
        task,source=row['task'],row['source'];require(digest(source)==row['source_sha256'],'source digest mismatch')
        require(row['receiver_reference_sha256']==digest(reference_source(task)),'reference differs')
        validate_owned_source(task,source)
        key=(task,row['source_sha256']);require(key not in seen,'duplicate source identity');seen.add(key)
        by_task[task].append(row)
    complete=set(selected)==set(TASK_BY_NAME)
    if complete:require(len(source_rows)==22095,'unexpected full source count')
    runtime=json.loads(subprocess.check_output(['node','-e','process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,platform:process.platform,arch:process.arch,versions:process.versions}))'],text=True))
    node_path=Path(shutil.which('node')).resolve();runtime['node_executable_sha256']=digest(node_path.read_bytes())
    runtime.update(python=platform.python_version(),operating_system=platform.platform(),machine=platform.machine(),cpu_count=os.cpu_count())
    out.mkdir(parents=True);(out/'raw').mkdir()
    started=time.monotonic()
    registration=dict(schema='markvalidity-native-completion-v1',started_at_utc=datetime.now(timezone.utc).isoformat(),
        tasks=selected,complete_frozen_design=complete,workers=workers,per_task_timeout_seconds=timeout,
        candidate_sources=len(source_rows),planned_candidate_input_calls=sum(len(domain_cases(r['task'])) for r in source_rows),
        observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,
        argument_model='immutable primitive strings and safe integer numbers only',
        isolation='new source factory invocation per input; exact frozen reference body plus bounded local-prefix grammar; trusted standard builtins and owned terminating controls; no arbitrary-code sandbox claim',
        output_model='tagged return or exception, exact canonical JSON comparison, one observation per frozen input',
        earlier_results_unchanged=True,
        input_sha256={str(p.relative_to(HERE)):digest(p.read_bytes()) for p in [evidence/'sources.jsonl.gz',evidence/'rows.csv.gz',
            evidence/'mixture_scores.csv',evidence/'pairwise_source_bounds.csv',retained/'raw/semantic_audit.csv']},
        producer_sha256={str(p.relative_to(HERE)):digest(p.read_bytes()) for p in [Path(__file__),HERE/'js/source_completion_runner.js',HERE/'src/covewm/tasks.py']},
        runtime=runtime)
    json_write(out/'registration.json',registration)
    specs=[];reference_snapshot={}
    for task in selected:
        cases=domain_cases(task);reference=reference_source(task)
        spec=dict(task=task,cases=cases,domain_sha256=digest(json.dumps(cases,ensure_ascii=False,separators=(',',':'))),
            nominal_cases=[list(args) for args in TASK_BY_NAME[task].nominal_cases],
            reference_sha256=digest(reference),observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,
            programs=[dict(id='reference',role='reference',source=reference,source_sha256=digest(reference))])
        for i,mutant in enumerate(TASK_BY_NAME[task].javascript_mutants,1):
            spec['programs'].append(dict(id=f'mutant-{i}',role='mutant',source=mutant,source_sha256=digest(mutant)))
        spec['programs'] += [dict(id=r['source_sha256'],role='candidate',source=r['source'],source_sha256=r['source_sha256'])
                             for r in sorted(by_task[task],key=lambda r:r['source_sha256'])]
        specs.append(spec)
        reference_snapshot[task]=dict(reference=reference,reference_sha256=digest(reference),
            cases=cases,nominal_cases=spec['nominal_cases'],domain_sha256=spec['domain_sha256'],mutants=list(TASK_BY_NAME[task].javascript_mutants))
    with gztext(out/'reference-domains.json.gz') as handle:handle.write(canonical(reference_snapshot)+'\n')
    executions=[]
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures={pool.submit(run_task,spec,out,timeout):spec['task'] for spec in specs}
            for future in as_completed(futures):
                receipt=future.result();executions.append(receipt)
                print(canonical(dict(task=receipt['task'],status='PASS',wall_seconds=receipt['wall_seconds'],
                    candidate_sources=receipt['worker_finish']['candidate_sources_executed'],
                    input_calls=receipt['worker_finish']['total_input_calls'])),flush=True)
        json_write(out/'execution.json',sorted(executions,key=lambda r:r['task']))
        summary=generate_summaries(out,evidence,retained)
        summary['wall_seconds']=round(time.monotonic()-started,6)
        summary['outputs_sha256']={str(p.relative_to(out)):digest(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='summary.json'}
        json_write(out/'summary.json',summary)
        print(canonical({k:summary[k] for k in ['status','complete_frozen_design','javascript_candidate_sources_executed',
            'javascript_candidate_input_calls','candidate_statuses','mutant_control_statuses','joint_exact','wall_seconds']}),flush=True)
        return summary
    except BaseException as exc:
        json_write(out/'failure.json',dict(status='FAILED_OR_PARTIAL',error=repr(exc),completed_tasks=[r['task'] for r in executions]))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,default=HERE/'results/revision-source-joint')
    parser.add_argument('--retained',type=Path,default=HERE/'results/revision-reproduction')
    parser.add_argument('--out',type=Path,default=HERE/'results/revision-native-completion')
    parser.add_argument('--tasks',nargs='+')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--timeout',type=int,default=1800)
    args=parser.parse_args()
    run(args.evidence,args.retained,args.out,args.tasks,args.workers,args.timeout)
