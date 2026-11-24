"""Check natural disclosure artifacts against rows and the exact Fraction prototype.

The primary implementation uses incremental integer counts and ratio buckets;
this receiver reconstructs every first-certificate state from the public rows
and evaluates the independently tested nonincremental Fraction implementation.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction as F
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path

from conditional_bounds import UnknownGroup, ScoreModel, conditional_bounds, conditional_comparison, joint_comparison

ALIASES = {'stock': 'stock', 's1': 's1', 's1_literal_predecessor': 's1',
           's4': 's4', 's4_return_boundary': 's4', 's1_s4': 's1_s4'}
CERTIFICATES = {'left_strict', 'right_strict', 'tie'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def array_sha(array):
    return sha(json.dumps(array, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def label(value):
    if value is True or type(value) is int and value == 1 or value == 'supported': return True
    if value is False or type(value) is int and value == 0 or value == 'contradicted': return False
    if value is None or value == 'unavailable': return None
    raise ValueError('unexpected input validity label')


def as_fraction(value):
    return None if value is None else F(value)


def reconstruct(coefficients, admitted, behavior=False):
    known_n = known_a = 0
    unknown = []
    for group, (n, a) in coefficients.items():
        if behavior: n = a
        if group in admitted:
            if admitted[group]:
                known_n += n
                known_a += a
        else:
            unknown.append(UnknownGroup(group, F(a), F(n)))
    return ScoreModel(F(known_n), F(known_a), tuple(unknown))


def check_snapshot(snapshot, left, right, admitted):
    models = (reconstruct(left, admitted), reconstruct(right, admitted))
    result = joint_comparison(*models)
    assert result['lower'] == F(snapshot['coupled_J']['lower'])
    assert result['upper'] == F(snapshot['coupled_J']['upper'])
    assert result['relation'] == snapshot['coupled_J']['decision']
    behavior = joint_comparison(reconstruct(left, admitted, True), reconstruct(right, admitted, True))
    assert behavior['lower'] == F(snapshot['coupled_A']['lower'])
    assert behavior['upper'] == F(snapshot['coupled_A']['upper'])
    assert behavior['relation'] == snapshot['coupled_A']['decision']
    for name, model in zip(('left', 'right'), models):
        c = conditional_bounds(model)
        observed = snapshot[f'{name}_C']
        assert (c['lower'], c['upper']) == (as_fraction(observed['lower']), as_fraction(observed['upper']))
        assert c['defined_for_all_completions'] == observed['defined_all']
        assert c['defined_for_some_completion'] == observed['defined_some']
    c = conditional_comparison(*models)
    observed = snapshot['coupled_C']
    reference_decision = ('undefined_everywhere_for_at_least_one_side'
                          if c['decision'] == 'undefined_everywhere' else c['decision'])
    assert reference_decision == observed['decision']
    if c['route'] == 'exact_common_remainder':
        assert observed['route'] == c['route']
        assert c['margin_lower'] == as_fraction(observed['lower'])
        assert c['margin_upper'] == as_fraction(observed['upper'])
        assert c['relation_on_defined_completions'] == observed['relation_on_defined']
    else:
        assert observed['route'] == 'individual_intervals_sufficient_only'
    assert len(c['audit_groups_to_common_remainder']) == snapshot['coefficient_different_unresolved']


def verify(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    input_base = (root / manifest.get('input_path_base_from_analysis', '.')).resolve()
    all_rows = []
    truth = {}
    for item in manifest['inputs']:
        input_path = Path(item['rows_path'])
        if not input_path.is_absolute(): input_path = input_base / input_path
        data = input_path.read_bytes()
        assert sha(data) == item['rows_sha256']
        records = json.loads(data)
        all_rows.extend(records)
        for row in records:
            v = label(row['validity_label'])
            g = row['source_contract_sha256']
            if g in truth and truth[g] is not None and v is not None:
                assert truth[g] == v
            if g not in truth or truth[g] is None: truth[g] = v
    groups = json.loads((root / 'group_index.json').read_text())
    identities = [g['source_contract_sha256'] for g in groups]
    reports = json.loads((root / 'comparisons.json').read_text())
    cases = policies = traces = certificates = reconstructed_states = 0
    for case, report in reports.items():
        rows = [r for r in all_rows if (report['scope'] == 'pooled'
                or r['dataset'].lower().replace('_sanitized', '') == report['scope'])
                and ALIASES[r['variant']] in (report['left'], report['right'])]
        coefs = {report['left']: defaultdict(lambda: [0, 0]), report['right']: defaultdict(lambda: [0, 0])}
        for row in rows:
            a = coefs[ALIASES[row['variant']]][row['source_contract_sha256']]
            a[0] += row['detected']
            a[1] += 1
        left, right = coefs[report['left']], coefs[report['right']]
        universe = set(left) | set(right)
        initial = ({r['source_contract_sha256']: True for r in rows
                    if r['candidate_sha256'] == r['reference_sha256']}
                   if manifest['initialization'] == 'reference_identity_known' else {})
        assert all(truth[g] is True for g in initial)
        check_snapshot(report['initial_snapshot'], left, right, initial)
        reconstructed_states += 1
        full_gap_j = sum(a for g, (a, b) in left.items() if truth[g]) - sum(a for g, (a, b) in right.items() if truth[g])
        full_gap_a = sum(b for g, (a, b) in left.items() if truth[g]) - sum(b for g, (a, b) in right.items() if truth[g])
        # The final natural inputs have no unavailable labels. This assertion is
        # an input check for this empirical receiving run, not a general premise
        # of the algorithm, which is checked with unknown labels separately.
        assert all(truth[g] is not None for g in universe)
        for policy, run in report['schedules'].items():
            schedule = run['schedule']
            order = [identities[i] for i in schedule]
            assert len(order) == len(set(order))
            assert set(order) == universe - set(initial)
            assert array_sha(schedule) == run['schedule_sha256']
            path = root / 'traces' / run['trace_file']
            assert sha(path.read_bytes()) == run['trace_sha256']
            found = {}
            with gzip.open(path, 'rt', newline='') as f:
                for step, row in enumerate(csv.DictReader(f)):
                    assert int(row['step']) == step
                    if step:
                        assert int(row['group_index']) == schedule[step - 1]
                        assert int(row['received_label']) == truth[order[step - 1]]
                    assert int(row['coupled_J_lower']) <= full_gap_j <= int(row['coupled_J_upper'])
                    assert int(row['coupled_A_lower']) <= full_gap_a <= int(row['coupled_A_upper'])
                    for metric in ('J', 'A'):
                        assert int(row[f'independent_{metric}_lower']) <= int(row[f'coupled_{metric}_lower'])
                        assert int(row[f'coupled_{metric}_upper']) <= int(row[f'independent_{metric}_upper'])
                    for method in ('independent', 'coupled'):
                        for metric in ('J', 'A', 'C'):
                            key = f'{method}_{metric}'
                            if row[f'{key}_decision'] in CERTIFICATES and key not in found:
                                found[key] = step
                    traces += 1
            assert step == len(schedule)
            assert set(found) == set(run['first_certificates'])
            reconstructed = set()
            for key, certificate in run['first_certificates'].items():
                step = certificate['suite_queries']
                assert found[key] == step
                assert array_sha(schedule[:step]) == certificate['schedule_prefix_sha256']
                if step not in reconstructed:
                    admitted = dict(initial)
                    admitted.update({g: truth[g] for g in order[:step]})
                    check_snapshot(certificate['snapshot'], left, right, admitted)
                    reconstructed.add(step)
                    reconstructed_states += 1
                assert certificate['decision'] == certificate['snapshot'][key]['decision']
                certificates += 1
            check_snapshot(run['final_snapshot'], left, right, {g: truth[g] for g in universe})
            reconstructed_states += 1
            policies += 1
        cases += 1
        print(f'{case}: reconstructed certificates and all trace prefixes PASS', flush=True)
    result = dict(status='PASS', analysis=os.path.relpath(root.resolve(), input_base), cases=cases, schedules=policies,
                  trace_states_checked=traces, first_certificates_checked=certificates,
                  independently_reconstructed_states=reconstructed_states,
                  method='Rebuilt coefficient/known-label models from original normalized rows at every first-certificate prefix; compared against the nonincremental exact-Fraction prototype; inspected every trace prefix for truth containment and cross-version interval nesting.',
                  files_sha256={name: sha((root / name).read_bytes()) for name in
                                ('manifest.json', 'comparisons.json', 'group_index.json', 'comparison_summary.csv')},
                  verifier_sha256=sha(Path(__file__).read_bytes()),
                  prototype_sha256=sha((Path(__file__).parent / 'conditional_bounds.py').read_bytes()))
    (root / 'certificate_receiving.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    if not __debug__: raise SystemExit('Run without -O.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    args = parser.parse_args()
    verify(args.analysis)
