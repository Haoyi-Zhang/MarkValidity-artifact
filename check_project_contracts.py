#!/usr/bin/env python3
"""Execute a call-contract audit on three previously frozen project modules.

The module sources and rename targets come from the existing transfer manifest.
This experiment observes declared calls, not complete project behavior. Sources
are compiled once and initialized in a fresh module namespace for every call.
The independent receiving mode executes saved sources without regenerating edits.
"""
from __future__ import annotations

import argparse
import ast
import copy
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from covewm.extended import syntax_aware_local_rename, inert_trailing_comment

SELECTED = ('attrs-01', 'idna-02', 'jmespath-01')
VARIANTS = ('reference', 'trailing-comment', 'parameter-rename', 'signature-preserving-alias')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def typed(value):
    """Preserve the builtin return distinctions observed by this contract."""
    if value is None:
        return {'type': 'none'}
    if type(value) in (bool, int, str):
        return {'type': type(value).__name__, 'value': value}
    if type(value) in (tuple, list):
        return {'type': type(value).__name__, 'items': [typed(v) for v in value]}
    if type(value) is dict and all(type(k) is str for k in value):
        return {'type': 'dict', 'items': [[k, typed(value[k])] for k in sorted(value)]}
    raise TypeError('observation type is outside the declared project contract')


def project_cases(module):
    if module == 'attrs-01':
        return [[False], [True]]
    if module == 'idna-02':
        return [[list(values)] for length in range(5)
                for values in itertools.product(range(5), repeat=length)]
    if module == 'jmespath-01':
        nodes = [{'type': 'literal', 'value': 0}, {'type': 'literal', 'value': 1},
                 {'type': 'current', 'children': []}]
        return [[name, copy.deepcopy(left), copy.deepcopy(right)]
                for name in ('eq', 'ne', 'lt', 'lte', 'gt', 'gte')
                for left in nodes for right in nodes]
    raise ValueError('unknown project contract')


def observation(code, specification, arguments, convention):
    namespace = {'__name__': '__markvalidity_project_contract__'}
    args = copy.deepcopy(arguments)
    try:
        exec(code, namespace)
        function = namespace[specification['function']]
        if convention == 'positional':
            value = function(*args)
        elif convention == 'keyword':
            value = function(**dict(zip(specification['argument_names'], args)))
        else:
            raise ValueError('unknown calling convention')
        result = {'kind': 'return', 'value': typed(value)}
        if specification['state_observer'] is not None:
            result['observed_state'] = typed(namespace[specification['state_observer']]())
        return result
    except Exception as error:
        return {'kind': 'exception', 'class': type(error).__name__, 'message': str(error)}


def alias_repair(renamed, function_name, old_name, new_name):
    """Preserve the external argument, introduce its fresh internal alias."""
    tree = ast.parse(renamed)
    target = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function_name)
    argument = next(a for a in target.args.args if a.arg == new_name)
    argument.arg = old_name
    position = int(isinstance(target.body[0], ast.Expr)
                   and isinstance(target.body[0].value, ast.Constant)
                   and isinstance(target.body[0].value.value, str))
    target.body.insert(position, ast.Assign(targets=[ast.Name(id=new_name, ctx=ast.Store())],
                                           value=ast.Name(id=old_name, ctx=ast.Load())))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'


def produce(output):
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'sources').mkdir()
    records = {r['module_id']: r for r in csv.DictReader((ROOT / 'corpus/transfer_manifest.csv').open())}
    specification = {
        'schema': 'markvalidity-project-call-contract-v1',
        'selection': 'Three existing frozen transfer targets whose complete modules use only builtin or standard-library dependencies; chosen to exercise keyword calls on existing parameter-rename controls.',
        'scope': 'Finite call-contract counterexamples on frozen module bytes, not a sample estimate of defect prevalence or whole-project behavior.',
        'initialization': 'Fresh module namespace and deep-copied arguments for every invocation; imported bisect is read-only.',
        'observation': 'Disjoint return/exception envelopes; builtin return types retained recursively; attrs setter additionally observed through its existing getter.',
        'runtime': platform.python_implementation() + ' ' + platform.python_version(),
        'projects': [],
    }
    rows = []
    for module in SELECTED:
        source_record = records[module]
        path = ROOT / 'corpus/transfer' / source_record['project_slug'] / f"module-{int(source_record['selection_rank']):02d}.py"
        reference = path.read_text()
        assert sha(reference) == source_record['source_sha256']
        tree = ast.parse(reference)
        target = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                      and n.lineno == int(source_record['rename_function_line']))
        replacement = 'cvlocal' + source_record['source_sha256'][:7]
        renamed = syntax_aware_local_rename(reference, target.lineno, source_record['rename_parameter'], replacement)
        sources = {'reference': reference, 'trailing-comment': inert_trailing_comment(reference),
                   'parameter-rename': renamed,
                   'signature-preserving-alias': alias_repair(renamed, target.name, source_record['rename_parameter'], replacement)}
        cases = project_cases(module)
        project = {'module_id': module, 'project': source_record['project'],
                   'version': source_record['version'], 'frozen_source': str(path.relative_to(ROOT)),
                   'frozen_source_sha256': sha(reference), 'function': target.name,
                   'argument_names': [a.arg for a in target.args.args],
                   'renamed_parameter': source_record['rename_parameter'], 'fresh_alias': replacement,
                   'state_observer': 'get_run_validators' if module == 'attrs-01' else None,
                   'cases': cases, 'domain_sha256': sha(canonical(cases)),
                   'calling_conventions': ['positional', 'keyword'], 'sources': {}}
        for variant, source in sources.items():
            relative = f'sources/{module}_{variant}.py'
            (output / relative).write_text(source)
            project['sources'][variant] = {'path': relative, 'sha256': sha(source), 'parses_and_compiles': True}
        contract = {k: project[k] for k in ('module_id', 'function', 'argument_names', 'state_observer', 'domain_sha256', 'calling_conventions')}
        contract.update({k: specification[k] for k in ('initialization', 'observation', 'runtime')})
        project['contract_sha256'] = sha(canonical(contract))
        codes = {variant: compile(source, f'<{module}:{variant}>', 'exec') for variant, source in sources.items()}
        for index, case in enumerate(cases):
            for convention in project['calling_conventions']:
                expected = observation(codes['reference'], project, case, convention)
                assert expected['kind'] == 'return', (module, index, convention, expected)
                for variant, code in codes.items():
                    actual = expected if variant == 'reference' else observation(code, project, case, convention)
                    rows.append({'module_id': module, 'variant': variant, 'case_index': index,
                                 'calling_convention': convention, 'source_sha256': project['sources'][variant]['sha256'],
                                 'contract_sha256': project['contract_sha256'], 'expected': canonical(expected),
                                 'actual': canonical(actual), 'matches': int(actual == expected)})
        specification['projects'].append(project)
    (output / 'contracts.json').write_text(json.dumps(specification, ensure_ascii=False, indent=2) + '\n')
    with gzip.open(output / 'observations.csv.gz', 'wt', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    summary = summarize(rows)
    summary.update({'status': 'PASS', 'scope': specification['scope'], 'module_count': len(SELECTED),
                    'case_count': sum(len(p['cases']) for p in specification['projects']),
                    'actual_native_invocations': len(rows), 'elapsed_seconds': round(time.monotonic() - started, 3),
                    'producer_sha256': sha(Path(__file__).read_bytes()),
                    'contracts_sha256': sha((output / 'contracts.json').read_bytes()),
                    'observations_sha256': sha((output / 'observations.csv.gz').read_bytes())})
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def summarize(rows):
    counts = []
    for module in SELECTED:
        for variant in VARIANTS:
            for convention in ('positional', 'keyword'):
                selected = [r for r in rows if (r['module_id'], r['variant'], r['calling_convention']) == (module, variant, convention)]
                counts.append({'module_id': module, 'variant': variant, 'calling_convention': convention,
                               'calls': len(selected), 'matching_observations': sum(int(r['matches']) for r in selected)})
    return {'outcomes': counts, 'observation_rows': len(rows)}


def verify(output):
    """Receive saved source and calls; do not call either edit constructor."""
    specification = json.loads((output / 'contracts.json').read_text())
    summary = json.loads((output / 'summary.json').read_text())
    assert sha((output / 'contracts.json').read_bytes()) == summary['contracts_sha256']
    assert sha((output / 'observations.csv.gz').read_bytes()) == summary['observations_sha256']
    with gzip.open(output / 'observations.csv.gz', 'rt') as handle:
        rows = list(csv.DictReader(handle))
    rowmap = {(r['module_id'], r['variant'], int(r['case_index']), r['calling_convention']): r for r in rows}
    assert len(rowmap) == len(rows)
    checked = 0
    for project in specification['projects']:
        assert sha(canonical(project['cases'])) == project['domain_sha256']
        for variant, source_record in project['sources'].items():
            source = (output / source_record['path']).read_text()
            assert sha(source) == source_record['sha256']
            code = compile(source, f"<{project['module_id']}:{variant}>", 'exec')
            for index, case in enumerate(project['cases']):
                for convention in project['calling_conventions']:
                    row = rowmap[(project['module_id'], variant, index, convention)]
                    observed = observation(code, project, case, convention)
                    assert canonical(observed) == row['actual']
                    expected = rowmap[(project['module_id'], 'reference', index, convention)]['actual']
                    assert row['expected'] == expected
                    assert int(row['matches']) == int(row['actual'] == expected)
                    assert row['source_sha256'] == source_record['sha256']
                    assert row['contract_sha256'] == project['contract_sha256']
                    checked += 1
    assert checked == len(rows) == summary['actual_native_invocations']
    assert summarize(rows)['outcomes'] == summary['outcomes']
    return {'status': 'PASS', 'saved_source_files_executed': 12, 'native_calls_reexecuted': checked,
            'edit_generators_called': 0, 'scope': 'Saved-source native replay and row/summary reconstruction under the recorded finite call contracts.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'results/revision-project-contracts')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = verify(args.out) if args.verify else produce(args.out)
    print(json.dumps(result, indent=2))
