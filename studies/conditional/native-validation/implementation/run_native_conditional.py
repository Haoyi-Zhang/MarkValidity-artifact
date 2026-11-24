#!/usr/bin/env python3
"""Fresh native conditional audits with balanced method order.

The registry contains emitted-source/contract bindings and reference evidence,
not candidate labels. Six repetitions per case and method give each method
three first and three second positions. This runner uses the retained native
worker and admission implementation without changing either historic source.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import sys
import time

from paired_conditional import PairedEnvelope


def load_module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeats', type=int, choices=(1, 6), default=6,
                        help='1 is execution validation; 6 is the balanced timing design')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('a new output directory is required')
    root = args.artifact.resolve()
    method_dir = root / 'external-studies/sew_natural/comparison_costs'
    sys.path.insert(0, str(method_dir))
    from policies import initialize, target_bounds
    import admission
    native = load_module('retained_native', method_dir / 'native_timing.py')
    api, module_path = native.load_api(root)
    runners = {'humaneval': root / 'external-studies/sew_natural/scripts/humaneval/native_runner_v3.py',
               'mbpp': root / 'external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'}
    environment = {'python': platform.python_version(), 'sys_version': sys.version,
                   'platform': platform.platform(), 'cpu_count_reported': os.cpu_count(),
                   'interpreter_executable_sha256': native.sha(Path(sys.executable).resolve().read_bytes())}
    for path in ('/sys/fs/cgroup/cpu.max', '/sys/fs/cgroup/memory.max'):
        try:
            environment[path] = Path(path).read_text().strip()
        except OSError:
            pass
    cases = [('HumanEval', 'humaneval', 'stock', 's1'),
             ('mbpp_sanitized', 'mbpp', 'stock', 's4')]
    order = []
    for repeat in range(args.repeats):
        # Both case position and within-case method order alternate. For six
        # repeats, every method is first three times within each case.
        for dataset, scope, left, right in (cases if repeat % 2 == 0 else list(reversed(cases))):
            methods = ('paired', 'independent') if repeat % 2 == 0 else ('independent', 'paired')
            for method in methods:
                order.append({'repeat': repeat + 1, 'dataset': dataset, 'scope': scope,
                              'left': left, 'right': right, 'target': 'C', 'method': method})
    args.out.mkdir(parents=True)
    source_paths = {'run_native_conditional.py': Path(__file__),
                    'paired_conditional.py': Path(__file__).with_name('paired_conditional.py'),
                    'native_timing.py': method_dir / 'native_timing.py',
                    'policies.py': method_dir / 'policies.py',
                    'admission.py': method_dir / 'admission.py',
                    'natural_analysis.py': module_path, **runners}
    snapshot = args.out / 'implementation'
    snapshot.mkdir()
    for name, source in source_paths.items():
        shutil.copy2(source, snapshot / (name if name.endswith('.py') else name + '.py'))
    protocol = {'status': 'frozen_before_execution', 'design': 'balanced_native_timing' if args.repeats == 6 else 'execution_validation',
                'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'run_order': order, 'environment': environment,
                'source_sha256': {name: native.sha(path.read_bytes()) for name, path in source_paths.items()},
                'public_registry_sha256': native.sha(args.registry.read_bytes()),
                'initialization': 'qualified_reference_identity_only',
                'cross_run_candidate_label_reuse': False,
                'timing_scope': 'From per-run coefficient/state construction through selection, comparison inference, native suite execution, admission and raw recording at first certificate. Common registry preparation is separate. Generation, detector evaluation and reference qualification precede this audit.',
                'method_descriptions': {
                    'paired': 'Original coefficient-differences-first policy with the paired ratio-envelope certificate and retained separate-interval rule.',
                    'independent': 'Original public minimax next-step separate-conditional-width policy and separate conditional certificate.'},
                'load_before': native.load_snapshot()}
    native.write(args.out / 'protocol.json', protocol)
    registry, rows, sources, contracts, setup = native.load_public(api, root, args.registry.resolve())
    native.write(args.out / 'common-registration.json', setup)
    groups = registry['groups']
    outcomes = []
    for ordinal, planned in enumerate(order, 1):
        name = f"{ordinal:02d}-{planned['scope']}-{planned['method']}"
        folder = args.out / name
        (folder / 'observations').mkdir(parents=True)
        phases = dict.fromkeys(native.PHASES, 0.0)
        start = time.perf_counter()
        load_before = native.load_snapshot()
        tick = time.perf_counter()
        selected_rows = tuple(row for row in rows if row.dataset == planned['dataset'])
        coefficients = api.pair_coefficients(selected_rows, planned['left'], planned['right'])
        seeds = {g: True for g in set(coefficients[0]) | set(coefficients[1])
                 if groups[g]['candidate_sha256'] == groups[g]['reference_sha256']}
        method = 'coupled' if planned['method'] == 'paired' else 'independent'
        state, policy = initialize(api, coefficients, seeds, method, 'C')
        if planned['method'] == 'paired':
            state = PairedEnvelope(state)
        phases['register_seconds'] += time.perf_counter() - tick
        prefix, queries = [], []
        while True:
            tick = time.perf_counter()
            bounds = state.certify() if planned['method'] == 'paired' else target_bounds(api, state, 'independent', 'C')
            phases['bounds_seconds'] += time.perf_counter() - tick
            prefix.append({'step': len(queries), 'bounds': api.serial(bounds),
                           'groups_admitted': len(state.admitted)})
            if bounds['decision'] in api.CERTIFICATES:
                break
            tick = time.perf_counter()
            group = policy.next_group(state)
            phases['select_seconds'] += time.perf_counter() - tick
            if group is None:
                raise ValueError('queries exhausted without a conditional certificate')
            tick = time.perf_counter()
            runner, request, expected_tests = native.execution_request(
                planned['dataset'], group, groups, contracts, sources, runners, environment)
            execution = native.execute(runner, request)
            worker_seconds = time.perf_counter() - tick
            phases['worker_seconds'] += worker_seconds
            tick = time.perf_counter()
            label = (admission.humaneval(execution['stdout'], execution['returncode'], execution['interruption'])
                     if planned['dataset'] == 'HumanEval' else
                     admission.mbpp(execution['stdout'], expected_tests, execution['returncode'], execution['interruption']))
            state.reveal(group, label)
            phases['receive_seconds'] += time.perf_counter() - tick
            tick = time.perf_counter()
            evidence = dict(execution, group=group, received_label=label,
                            source_sha256=groups[group]['candidate_sha256'], contract_sha256=groups[group]['contract_sha256'],
                            worker_seconds=worker_seconds)
            evidence_file = folder / 'observations' / f'{len(queries) + 1:05d}.json'
            native.write(evidence_file, evidence)
            queries.append({'step': len(queries) + 1, 'group': group, 'received_label': label,
                            'evidence_file': evidence_file.relative_to(args.out).as_posix(),
                            'evidence_sha256': native.sha(evidence_file.read_bytes())})
            phases['record_seconds'] += time.perf_counter() - tick
        tick = time.perf_counter()
        native.write(folder / 'trace.json', prefix)
        phases['record_seconds'] += time.perf_counter() - tick
        elapsed = time.perf_counter() - start
        result = dict(planned, directory=name, candidate_suite_queries=len(queries), denominator=coefficients[2],
                      initial_reference_groups=len(seeds), decision=bounds['decision'],
                      final_certificate=api.serial(bounds), phase_seconds=phases,
                      audit_total_seconds=elapsed, unallocated_loop_seconds=elapsed - sum(phases.values()),
                      queries=queries, load_before=load_before, load_after=native.load_snapshot())
        native.write(folder / 'receipt.json', result)
        outcomes.append({k: v for k, v in result.items() if k != 'queries'})
        print(json.dumps({'case': planned['scope'], 'method': planned['method'], 'repeat': planned['repeat'],
                          'queries': len(queries), 'seconds': elapsed, 'decision': bounds['decision']}), flush=True)
    for name, source in source_paths.items():
        if native.sha(source.read_bytes()) != protocol['source_sha256'][name]:
            raise RuntimeError('executed implementation changed during measurement')
    summaries = []
    for scope in ('humaneval', 'mbpp'):
        for method in ('paired', 'independent'):
            selected = [r for r in outcomes if r['scope'] == scope and r['method'] == method]
            values = [r['audit_total_seconds'] for r in selected]
            summaries.append({'scope': scope, 'method': method, 'repetitions': len(values),
                              'queries': sorted({r['candidate_suite_queries'] for r in selected}),
                              'median_seconds': statistics.median(values), 'minimum_seconds': min(values),
                              'maximum_seconds': max(values),
                              'phase_medians': {p: statistics.median(r['phase_seconds'][p] for r in selected)
                                                for p in native.PHASES}})
    native.write(args.out / 'receipt.json', {'status': 'complete', 'runs': outcomes, 'summaries': summaries,
                 'total_candidate_suites': sum(r['candidate_suite_queries'] for r in outcomes),
                 'candidate_observation_files_read_before_selection': 0,
                 'cross_run_candidate_label_reuse': False,
                 'common_preparation_seconds': setup['total_seconds'],
                 'independent_receiving_required': True})


if __name__ == '__main__':
    main()
