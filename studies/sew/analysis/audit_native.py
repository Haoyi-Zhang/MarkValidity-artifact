#!/usr/bin/env python3
"""Execute only selected candidate suites from a label-free public registry.

This is a fresh receiving replay of predeclared comparisons, not a prospective
corpus discovery or an end-to-end speed benchmark. No retained candidate
observation file or validity label is read by this entry point.
"""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')

def mbpp_events(stdout, returncode, interruption):
    lines=stdout.splitlines();events=[]
    for index,line in enumerate(lines):
        if not line.strip():continue
        try:events.append(json.loads(line))
        except ValueError:
            if index==len(lines)-1 and (interruption or returncode!=0):
                # A killed writer can leave a partial final JSONL record.
                # Earlier complete records still supply admissible witnesses.
                break
            raise
    return events

def admit_mbpp(events, expected_tests, returncode, interruption):
    """Admit a retained witness before considering process completion."""
    if not all(isinstance(e,dict) for e in events):
        raise ValueError('malformed MBPP event')
    if any(e.get('status')=='evidence_rejected' for e in events):
        raise RuntimeError('MBPP observer rejected the contract evidence')
    compile_events=[e for e in events if e.get('event')=='source_compile']
    tests=[e for e in events if e.get('event')=='test_result']
    indices=[e.get('test_index') for e in tests]
    if len(compile_events)>1 or len(indices)!=len(set(indices)):
        raise ValueError('duplicate MBPP evidence')
    if any(type(i) is not int or not 0<=i<expected_tests for i in indices):
        raise ValueError('unexpected MBPP assertion index')
    if any(e.get('status')=='failed' for e in compile_events):
        return False
    if any(e.get('status')=='failed' and e.get('error',{}).get('phase') in
           {'initialize_source','original_assertion'} for e in tests):
        return False
    completed=[e for e in events if e.get('event')=='complete']
    if (returncode==0 and not interruption and len(completed)==1
        and len(compile_events)==1 and compile_events[0].get('status')=='passed'
        and len(tests)==expected_tests and all(e.get('status')=='passed' for e in tests)
        and completed[0].get('status')=='passed'
        and completed[0].get('completed_tests')==expected_tests
        and completed[0].get('scheduled_tests')==expected_tests):
        return True
    return None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--registry',type=Path,required=True)
    p.add_argument('--analysis-module',type=Path,required=True)
    p.add_argument('--humaneval-runner',type=Path,required=True)
    p.add_argument('--mbpp-runner',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();root=a.artifact.resolve()
    if a.out.exists():raise ValueError('fresh output directory required')
    spec=importlib.util.spec_from_file_location('native_comparison_analysis',a.analysis_module.resolve())
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    registry=json.loads(a.registry.read_text())
    forbidden={'validity_label','validity','candidate_status','joint','observation_path','candidate_elapsed_seconds','candidate_function_invocations','assertion_entries'}
    if any(forbidden&set(r) for r in registry['rows']):raise ValueError('candidate evidence leaked to public rows')
    rows=[]
    for r in registry['rows']:
        if type(r['suite_cost']) is not int or r['suite_cost']!=1:
            raise ValueError('unsupported public query cost')
        if type(r['detected']) is not bool:
            raise ValueError('unavailable public detector evidence')
        group=api.source_contract_id(r['reference_sha256'],r['candidate_sha256'],r['contract_sha256'])
        if group!=r['source_contract_sha256'] or group not in registry['groups']:
            raise ValueError('changed row-to-group identity')
        for field in ('reference_sha256','candidate_sha256','contract_sha256','dataset','task_id'):
            if r[field]!=registry['groups'][group][field]:
                raise ValueError('row and group metadata disagree')
        v=api.ALIASES[r['variant']]
        rows.append(api.PublicRow(r['dataset'],r['task_id'],r['key_id'],r['key_hex'],v,r['variant'],r['source_contract_sha256'],r['detected'],r['suite_cost'],r['input_index'],r['row_index']))
    api.validate_workload(rows)
    groups=registry['groups'];cache={}
    def asset(relative,expected=None):
        q=(root/relative).resolve()
        if not q.is_relative_to(root):raise ValueError('asset path escapes artifact')
        b=q.read_bytes()
        if expected and sha(b)!=expected:raise ValueError(f'changed asset {relative}')
        return b
    # Reference suites are qualified setup evidence, not candidate disclosures.
    for g,m in groups.items():
        expected=api.source_contract_id(m['reference_sha256'],m['candidate_sha256'],m['contract_sha256'])
        if expected!=g:raise ValueError('bad public group identity')
        asset(m['source_file'],m['candidate_sha256']);asset(m['reference_file'],m['reference_sha256'])
        contract=json.loads(asset(m['contract_file']))
        if sha(canonical(contract))!=m['contract_sha256']:raise ValueError('changed contract')
        rb=asset(m['reference_observation_file'],m['reference_observation_sha256'])
        if m['reference_observation_file'].endswith('.gz'):rb=gzip.decompress(rb)
        if json.loads(rb).get('status')!='passed':raise ValueError('unqualified reference')
        cache[g]=contract
    a.out.mkdir(parents=True)
    cases=[('HumanEval','stock','s1','J','joint_width_per_suite'),
           ('HumanEval','stock','s1','C','conditional_differences_first'),
           ('mbpp_sanitized','stock','s4','J','joint_width_per_suite'),
           ('mbpp_sanitized','stock','s4','C','conditional_differences_first')]
    environment=dict(python=platform.python_version(),sys_version=sys.version,platform=platform.platform(),
                     interpreter_executable_sha256=sha(Path(sys.executable).resolve().read_bytes()))
    report=[];t0=time.perf_counter()
    for dataset,left,right,target,policy_name in cases:
        name=f'{dataset}__{left}__{right}__{target}'
        folder=a.out/name;folder.mkdir();(folder/'observations').mkdir()
        selected=[r for r in rows if r.dataset==dataset]
        lc,rc,n,order=api.pair_coefficients(selected,left,right)
        state=api.PairState(lc,rc,n)
        seeds=[g for g in state.groups if groups[g]['candidate_sha256']==groups[g]['reference_sha256']]
        for g in sorted(seeds):state.reveal(g,True)
        policy=api.AuditPolicy(policy_name,state,order);queries=[];trace=[];started=time.perf_counter()
        while True:
            snapshot=state.snapshot();trace.append(api.serial(snapshot))
            decision=snapshot['coupled_'+target]['decision']
            if decision in api.CERTIFICATES:break
            g=policy.next_group(state)
            if g is None:break
            m=groups[g];contract=cache[g];source=asset(m['source_file'],m['candidate_sha256']).decode()
            if dataset=='HumanEval':
                runner=a.humaneval_runner.resolve();native=contract
                if sha(runner.read_bytes())!=native['observer_sha256']:raise ValueError('HumanEval observer differs from contract')
                if native.get('interpreter_executable_sha256')!=environment['interpreter_executable_sha256']:raise ValueError('HumanEval interpreter differs')
                if native.get('platform')!=environment['platform']:raise ValueError('HumanEval platform differs')
                request={'source':source,'test':native['test_body'],'entry_point':native['entry_point']}
            else:
                runner=a.mbpp_runner.resolve()
                native=contract.get('native_contract',contract.get('original_native_contract',contract))
                env=contract.get('execution_environment',native.get('execution_environment',{}))
                if not env or env.get('interpreter_executable_sha256')!=environment['interpreter_executable_sha256']:raise ValueError('MBPP interpreter differs')
                if env.get('platform')!=environment['platform']:raise ValueError('MBPP platform differs')
                if sha(runner.read_bytes())!=native['native_runner_sha256']:raise ValueError('MBPP observer differs')
                request={'source':source,'test_imports':native['test_imports'],'test_list':native['test_list']}
            child_env=os.environ.copy();child_env.pop('PYTHONPATH',None);child_env.pop('PYTHONOPTIMIZE',None)
            child_env.update(PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
            begin=time.perf_counter();interruption=None
            with tempfile.TemporaryDirectory(prefix='markvalidity-native-query-') as tmp:
                try:
                    run=subprocess.run([sys.executable,'-B','-S',str(runner)],cwd=tmp,env=child_env,
                        input=json.dumps(request),text=True,capture_output=True,timeout=15)
                    stdout,stderr,code=run.stdout,run.stderr,run.returncode
                except subprocess.TimeoutExpired as ex:
                    stdout,stderr,code=ex.stdout or '',ex.stderr or '',None;interruption='wall_timeout'
                    if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
                    if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
            label=None;result=None
            try:
                if dataset=='HumanEval':result=json.loads(stdout)
                else:
                    events=mbpp_events(stdout,code,interruption)
                    label=admit_mbpp(events,len(native['test_list']),code,interruption)
                if dataset=='HumanEval' and code==0 and not interruption and isinstance(result,dict):
                    if result.get('status')=='passed':label=True
                    elif result.get('status')=='failed':label=False
            except (ValueError,TypeError):interruption='invalid_observer_output'
            evidence=dict(group=g,source_sha256=m['candidate_sha256'],contract_sha256=m['contract_sha256'],
                          received_label=label,returncode=code,interruption=interruption,
                          stdout=stdout,stderr=stderr,elapsed_seconds=time.perf_counter()-begin)
            epath=folder/'observations'/f'{len(queries)+1:05d}-{g}.json';write(epath,evidence)
            queries.append(dict(step=len(queries)+1,group=g,received_label=label,
                                evidence_file=epath.relative_to(a.out).as_posix(),evidence_sha256=sha(epath.read_bytes())))
            state.reveal(g,label)
        outcome=dict(case=name,dataset=dataset,left=left,right=right,target=target,policy=policy_name,
                     denominator=n,initial_reference_groups=len(seeds),candidate_suite_queries=len(queries),
                     decision=decision,final_snapshot=api.serial(state.snapshot()),queries=queries,
                     seconds=time.perf_counter()-started)
        write(folder/'certificate.json',outcome);write(folder/'trace.json',trace)
        if decision not in api.CERTIFICATES:raise ValueError('native audit did not reach its requested certificate')
        report.append(outcome)
        print(json.dumps({k:outcome[k] for k in ('case','candidate_suite_queries','decision','seconds')}),flush=True)
    write(a.out/'receipt.json',dict(schema='markvalidity-native-comparison-receiving-v1',status='PASS',
        public_registry_sha256=sha(a.registry.read_bytes()),driver_sha256=sha(Path(__file__).read_bytes()),
        analysis_sha256=sha(a.analysis_module.read_bytes()),environment=environment,
        total_candidate_suite_queries=sum(r['candidate_suite_queries'] for r in report),
        candidate_observation_files_read_before_selection=0,seconds=time.perf_counter()-t0,
        scope='Independent fresh native receiving replay; reference qualification is shared setup. Separate cases start with reference-identity labels only; no candidate-query labels are shared across cases.',
        cases=[{k:v for k,v in r.items() if k!='queries'} for r in report]))

if __name__=='__main__':main()
