#!/usr/bin/env python3
"""Complementary serial native timing with each within-case method order reversed.

The timed scope begins with already emitted programs and detector decisions.
Embedding, detector evaluation, and reference execution are common prior work;
they are not reported as accelerated. Each audit starts with qualified exact
reference identities only. Candidate labels are never shared between runs.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time

from analyze import load_api
import admission
from policies import initialize, policy_name, target_bounds


CASES = [
    ('HumanEval', 'humaneval', 'stock', 's1', 'J'),
    ('HumanEval', 'humaneval', 'stock', 's1', 'C'),
    ('mbpp_sanitized', 'mbpp', 'stock', 's4', 'J'),
    ('mbpp_sanitized', 'mbpp', 'stock', 's4', 'C'),
]
FORBIDDEN = {'validity_label', 'validity', 'candidate_status', 'joint', 'observation_path',
             'candidate_elapsed_seconds', 'candidate_function_invocations', 'assertion_entries'}
PHASES = ('register_seconds', 'select_seconds', 'bounds_seconds', 'worker_seconds',
          'receive_seconds', 'record_seconds')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def sha(content):
    return hashlib.sha256(content).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def load_snapshot():
    sample = {'monotonic_seconds': time.perf_counter(), 'load_average': list(os.getloadavg()),
              'visible_processes': sum(p.name.isdigit() for p in Path('/proc').iterdir()),
              'producer_cpu_seconds': time.process_time()}
    try:
        sample['cpu_affinity'] = sorted(os.sched_getaffinity(0))
    except AttributeError:
        pass
    return sample


def load_public(api, root, registry_file):
    started = time.perf_counter()
    raw = registry_file.read_bytes()
    registry = json.loads(raw)
    parsed = time.perf_counter()
    groups, rows, sources, contracts = registry['groups'], [], {}, {}
    read_files = {}

    def asset(relative, expected=None):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('public asset escapes artifact')
        content = path.read_bytes()
        checksum = sha(content)
        if expected is not None and checksum != expected:
            raise ValueError('changed public asset: ' + relative)
        read_files[relative] = checksum
        return content

    for r in registry['rows']:
        if FORBIDDEN & set(r):
            raise ValueError('candidate result leaked into public row')
        if type(r['detected']) is not bool or type(r['suite_cost']) is not int or r['suite_cost'] != 1:
            raise ValueError('unsupported detector evidence or query cost')
        group = api.source_contract_id(r['reference_sha256'], r['candidate_sha256'], r['contract_sha256'])
        if group != r['source_contract_sha256'] or group not in groups:
            raise ValueError('changed row-group identity')
        for key in ('reference_sha256', 'candidate_sha256', 'contract_sha256', 'dataset', 'task_id'):
            if r[key] != groups[group][key]:
                raise ValueError('inconsistent group metadata')
        rows.append(api.PublicRow(r['dataset'], r['task_id'], r['key_id'], r['key_hex'],
                                 api.ALIASES[r['variant']], r['variant'], group, r['detected'], 1,
                                 r['input_index'], r['row_index']))
    api.validate_workload(rows)
    for group, m in groups.items():
        if FORBIDDEN & set(m):
            raise ValueError('candidate result leaked into public group')
        if api.source_contract_id(m['reference_sha256'], m['candidate_sha256'], m['contract_sha256']) != group:
            raise ValueError('changed public group identity')
        sources[group] = asset(m['source_file'], m['candidate_sha256']).decode()
        asset(m['reference_file'], m['reference_sha256'])
        contract = json.loads(asset(m['contract_file']))
        if sha(canonical(contract)) != m['contract_sha256']:
            raise ValueError('changed behavioral contract')
        ref = asset(m['reference_observation_file'], m['reference_observation_sha256'])
        if m['reference_observation_file'].endswith('.gz'):
            ref = gzip.decompress(ref)
        if json.loads(ref).get('status') != 'passed':
            raise ValueError('unqualified reference suite')
        contracts[group] = contract
    finished = time.perf_counter()
    return registry, tuple(rows), sources, contracts, {
        'public_registry_sha256': sha(raw), 'load_seconds': parsed - started,
        'validate_register_seconds': finished - parsed, 'total_seconds': finished - started,
        'public_rows': len(rows), 'public_groups': len(groups), 'asset_files_sha256': read_files,
        'candidate_observation_files_read': 0,
        'scope': 'Parse public rows and verify emitted/reference sources, contracts and qualified reference observations. No candidate result is available to this phase.'}


def execution_request(dataset, group, groups, contracts, sources, runners, environment):
    contract = contracts[group]
    if dataset == 'HumanEval':
        runner = runners['humaneval']
        if sha(runner.read_bytes()) != contract['observer_sha256']:
            raise ValueError('HumanEval observer changed')
        if contract.get('interpreter_executable_sha256') != environment['interpreter_executable_sha256'] or contract.get('platform') != environment['platform']:
            raise ValueError('HumanEval execution environment changed')
        return runner, {'source': sources[group], 'test': contract['test_body'], 'entry_point': contract['entry_point']}, None
    native = contract.get('native_contract', contract.get('original_native_contract', contract))
    env = contract.get('execution_environment', native.get('execution_environment', {}))
    runner = runners['mbpp']
    if env.get('interpreter_executable_sha256') != environment['interpreter_executable_sha256'] or env.get('platform') != environment['platform']:
        raise ValueError('MBPP execution environment changed')
    if sha(runner.read_bytes()) != native['native_runner_sha256']:
        raise ValueError('MBPP observer changed')
    return runner, {'source': sources[group], 'test_imports': native['test_imports'], 'test_list': native['test_list']}, len(native['test_list'])


def execute(runner, request):
    child_env = os.environ.copy()
    child_env.pop('PYTHONPATH', None)
    child_env.pop('PYTHONOPTIMIZE', None)
    child_env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    interruption = None
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with tempfile.TemporaryDirectory(prefix='markvalidity-cost-query-') as tmp:
        try:
            result = subprocess.run([sys.executable, '-B', '-S', str(runner)], cwd=tmp, env=child_env,
                                    input=json.dumps(request), text=True, capture_output=True, timeout=15)
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as ex:
            stdout, stderr, code, interruption = ex.stdout or '', ex.stderr or '', None, 'wall_timeout'
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors='replace')
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors='replace')
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'stdout': stdout, 'stderr': stderr, 'returncode': code, 'interruption': interruption,
            'child_user_cpu_seconds': usage_after.ru_utime - usage_before.ru_utime,
            'child_system_cpu_seconds': usage_after.ru_stime - usage_before.ru_stime}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--complement-of', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.repeats != 3:
        raise ValueError('use a fresh output tree and the fixed three-repeat design')
    root = args.artifact.resolve()
    api, module_path = load_api(root)
    analysis_dir = module_path.parent
    sys.path.insert(0, str(analysis_dir))
    runners = {'humaneval': root / 'external-studies/sew_natural/scripts/humaneval/native_runner_v3.py',
               'mbpp': root / 'external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'}
    environment = {'python': platform.python_version(), 'sys_version': sys.version,
                   'platform': platform.platform(), 'cpu_count_reported': os.cpu_count(),
                   'interpreter_executable_sha256': sha(Path(sys.executable).resolve().read_bytes())}
    for path in ('/sys/fs/cgroup/cpu.max', '/sys/fs/cgroup/memory.max'):
        try:
            environment[path] = Path(path).read_text().strip()
        except OSError:
            pass
    args.out.mkdir(parents=True)
    order = []
    for repeat in range(args.repeats):
        rotated = CASES[repeat:] + CASES[:repeat]
        for position, case in enumerate(rotated):
            methods = ('independent', 'coupled') if (repeat + position) % 2 == 0 else ('coupled', 'independent')
            for method in methods:
                dataset, scope, left, right, target = case
                order.append({'repeat': repeat + 1, 'dataset': dataset, 'scope': scope, 'left': left,
                              'right': right, 'target': target, 'method': method,
                              'policy': policy_name(method, target)})
    source_files = {'native_timing.py': Path(__file__).with_name('native_timing.py'),
                    'native_timing_reverse.py': Path(__file__), 'policies.py': Path(__file__).with_name('policies.py'),
                    'analyze.py': Path(__file__).with_name('analyze.py'), 'natural_analysis.py': module_path,
                    'admission.py': Path(__file__).with_name('admission.py'),
                    'humaneval_runner': runners['humaneval'], 'mbpp_runner': runners['mbpp']}
    prior_bytes = args.complement_of.read_bytes()
    prior = json.loads(prior_bytes)
    if prior['public_registry_sha256'] != sha(args.registry.read_bytes()) or prior['environment'] != environment:
        raise ValueError('complementary block must use identical public registry and runtime')
    if len(prior['run_order']) != len(order):
        raise ValueError('complementary block needs the complete earlier matrix')
    for index in range(0, len(order), 2):
        if order[index:index+2] != list(reversed(prior['run_order'][index:index+2])):
            raise ValueError('second block must reverse each case pair and preserve case order')
    for name, checksum in prior['source_sha256'].items():
        if sha(source_files[name].read_bytes()) != checksum:
            raise ValueError('complementary block changed a frozen dependency: ' + name)
    snapshots = args.out / 'source-snapshots'
    snapshots.mkdir()
    inventory = {}
    for name, path in source_files.items():
        content = path.read_bytes()
        (snapshots / name).write_bytes(content)
        inventory[name] = {'original_path': path.resolve().relative_to(root).as_posix(),
                           'snapshot_file': name, 'sha256': sha(content)}
    write(snapshots / 'manifest.json', {
        'schema': 'markvalidity-native-source-snapshots-v1',
        'capture_scope': 'Captured before complementary-block candidate execution.',
        'files': inventory})
    protocol = {'schema': 'markvalidity-serial-comparison-cost-protocol-v1', 'status': 'FROZEN_BEFORE_EXECUTION',
                'counterbalance_block': 'complementary_reverse_order',
                'complement_of_protocol_sha256': sha(prior_bytes),
                'source_snapshot_manifest_sha256': sha((snapshots / 'manifest.json').read_bytes()),
                'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_sha256': {name: sha(path.read_bytes()) for name, path in source_files.items()},
                'public_registry_sha256': sha(args.registry.read_bytes()), 'environment': environment,
                'run_order': order, 'repeats': args.repeats, 'runs': len(order),
                'initialization': 'qualified_reference_identity_only', 'candidate_label_cache_between_runs': False,
                'scope': 'Additional comparison audit from frozen emitted sources and detector decisions, with common qualified reference evidence. No embedding/detection generation speed or population timing inference.',
                'phase_definitions': {
                    'common_load_register': 'Public registry parsing, source/contract/reference-observation hashing and row registration, performed once and reported separately.',
                    'register_seconds': 'Per-run coefficient construction, reference-identity admission, target state and method-specific policy initialization.',
                    'select_seconds': 'Choose the next group from public state before executing it.',
                    'bounds_seconds': 'Compute only this method and target\'s current bound and stopping decision.',
                    'worker_seconds': 'Build and validate the frozen request, launch the isolated subprocess, capture output and clean its temporary directory; includes launch overhead.',
                    'receive_seconds': 'Parse the new stdout and admit its result into the method state.',
                    'record_seconds': 'Serialize and write raw observations and trace records.',
                    'audit_total_seconds': 'Wall time from per-run registration through the certified stop, including the measured phases and loop overhead.'},
                'load_before': load_snapshot()}
    write(args.out / 'protocol.json', protocol)
    print(json.dumps({'event': 'timing_started', 'runs': len(order), 'protocol_sha256': sha((args.out / 'protocol.json').read_bytes())}), flush=True)
    registry, rows, sources, contracts, setup = load_public(api, root, args.registry.resolve())
    write(args.out / 'common-registration.json', setup)
    groups = registry['groups']
    results = []
    for ordinal, planned in enumerate(order, start=1):
        name = f"{ordinal:02d}-r{planned['repeat']}-{planned['scope']}-{planned['left']}-{planned['right']}-{planned['target']}-{planned['method']}"
        folder = args.out / name
        folder.mkdir()
        (folder / 'observations').mkdir()
        dataset, method, target = planned['dataset'], planned['method'], planned['target']
        run_begin = time.perf_counter()
        phases = dict.fromkeys(PHASES, 0.0)
        before = load_snapshot()
        tick = time.perf_counter()
        selected_rows = tuple(r for r in rows if r.dataset == dataset)
        coefficients = api.pair_coefficients(selected_rows, planned['left'], planned['right'])
        seeds = {g: True for g in set(coefficients[0]) | set(coefficients[1])
                 if groups[g]['candidate_sha256'] == groups[g]['reference_sha256']}
        state, policy = initialize(api, coefficients, seeds, method, target)
        phases['register_seconds'] += time.perf_counter() - tick
        queries, prefix = [], []
        while True:
            tick = time.perf_counter()
            bounds = target_bounds(api, state, method, target)
            phases['bounds_seconds'] += time.perf_counter() - tick
            prefix.append({'step': len(queries), 'bounds': api.serial(bounds),
                           'groups_admitted': len(state.admitted)})
            if bounds['decision'] in api.CERTIFICATES:
                break
            tick = time.perf_counter()
            group = policy.next_group(state)
            phases['select_seconds'] += time.perf_counter() - tick
            if group is None:
                raise ValueError('the declared native comparison exhausted its queries without a certificate')
            tick = time.perf_counter()
            runner, request, expected_tests = execution_request(dataset, group, groups, contracts, sources, runners, environment)
            execution = execute(runner, request)
            worker_seconds = time.perf_counter() - tick
            phases['worker_seconds'] += worker_seconds
            tick = time.perf_counter()
            label = None
            if dataset == 'HumanEval':
                label = admission.humaneval(execution['stdout'], execution['returncode'], execution['interruption'])
            else:
                label = admission.mbpp(execution['stdout'], expected_tests, execution['returncode'], execution['interruption'])
            state.reveal(group, label)
            phases['receive_seconds'] += time.perf_counter() - tick
            tick = time.perf_counter()
            evidence = dict(execution, group=group, received_label=label,
                            source_sha256=groups[group]['candidate_sha256'], contract_sha256=groups[group]['contract_sha256'],
                            worker_seconds=worker_seconds)
            evidence_file = folder / 'observations' / f'{len(queries)+1:05d}-{group}.json'
            write(evidence_file, evidence)
            queries.append({'step': len(queries) + 1, 'group': group, 'received_label': label,
                            'evidence_file': evidence_file.relative_to(args.out).as_posix(),
                            'evidence_sha256': sha(evidence_file.read_bytes())})
            phases['record_seconds'] += time.perf_counter() - tick
        tick = time.perf_counter()
        write(folder / 'trace.json', prefix)
        phases['record_seconds'] += time.perf_counter() - tick
        elapsed = time.perf_counter() - run_begin
        outcome = dict(planned, ordinal=ordinal, directory=name, denominator=coefficients[2],
                       initial_reference_groups=len(seeds), candidate_suite_queries=len(queries),
                       decision=bounds['decision'], final_bounds=api.serial(bounds), phase_seconds=phases,
                       audit_total_seconds=elapsed, unallocated_loop_seconds=elapsed-sum(phases.values()),
                       queries=queries, trace_sha256=sha((folder/'trace.json').read_bytes()),
                       load_before=before, load_after=load_snapshot())
        write(folder / 'receipt.json', outcome)
        results.append({k: value for k, value in outcome.items() if k != 'queries'})
        print(json.dumps({'event': 'run_complete', 'ordinal': ordinal, 'run': name,
                          'queries': len(queries), 'seconds': elapsed, 'decision': bounds['decision']}), flush=True)
    for name, path in source_files.items():
        if sha(path.read_bytes()) != protocol['source_sha256'][name]:
            raise ValueError('implementation changed during the timing run: ' + name)
    write(args.out / 'receipt.json', {'schema': 'markvalidity-serial-native-comparison-costs-v1', 'status': 'COMPLETE',
          'protocol_sha256': sha((args.out / 'protocol.json').read_bytes()),
          'common_registration_sha256': sha((args.out / 'common-registration.json').read_bytes()),
          'public_registry_sha256': setup['public_registry_sha256'], 'candidate_observation_files_read_before_selection': 0,
          'cross_run_candidate_label_reuse': False, 'runs': results,
          'total_candidate_suite_queries': sum(row['candidate_suite_queries'] for row in results),
          'load_after': load_snapshot(), 'independent_receiving_required': True})
    print(json.dumps({'event': 'timing_complete', 'runs': len(results),
                      'total_candidate_suites': sum(row['candidate_suite_queries'] for row in results)}), flush=True)


if __name__ == '__main__':
    main()
