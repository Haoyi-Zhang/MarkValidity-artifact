#!/usr/bin/env python3
"""Receive fresh native conditional audits without importing producer methods."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


CERTIFICATES = {'left_strict', 'right_strict', 'tie'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def serial(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {k: serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return value


def bounded(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root), 'input escapes its declared directory')
    return path


def load_module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def independent_paired(left, right, admitted, reference):
    """Fraction reconstruction from distinct group coefficients, without index."""
    lm, rm = reference.compact_pair(left, right, admitted)
    lc, rc = reference.conditional_bounds(lm), reference.conditional_bounds(rm)
    defined = lc['defined_for_all_completions'] and rc['defined_for_all_completions']
    result = {'route': 'paired_ratio_envelope', 'defined_all': defined,
              'anchors': {}, 'decision': 'unresolved', 'anchor': None, 'decision_source': None}
    if not lc['defined_for_some_completion'] or not rc['defined_for_some_completion']:
        result['decision'] = 'undefined_everywhere_for_at_least_one_side'
        return result
    remaining = (set(left) | set(right)) - set(admitted)
    delta = []
    for group in sorted(remaining):
        al, bl = left.get(group, (0, 0))
        ar, br = right.get(group, (0, 0))
        if (al, bl) != (ar, br):
            delta.append((Fraction(al - ar), Fraction(bl - br)))
    dn = lm.known_joint - rm.known_joint
    dm = lm.known_valid - rm.known_valid
    decisions = []
    for name, score in [('left', lc), ('right', rc)]:
        endpoints, lows, highs = [], [], []
        for q in dict.fromkeys((score['lower'], score['upper'])):
            values = [c - q * d for c, d in delta]
            lower = dn - q * dm + sum((x for x in values if x < 0), Fraction())
            upper = dn - q * dm + sum((x for x in values if x > 0), Fraction())
            lo_num, hi_num = lower * q.denominator, upper * q.denominator
            require(lo_num.denominator == hi_num.denominator == 1, 'integer-count receiver got fractional scaled endpoints')
            endpoints.append({'q': q, 'lower_numerator': int(lo_num),
                              'upper_numerator': int(hi_num), 'denominator': q.denominator})
            lows.append(lower)
            highs.append(upper)
        relation = reference.relation(min(lows), max(highs))
        result['anchors'][name] = {'lower': min(lows), 'upper': max(highs), 'endpoints': endpoints,
                                   'different_unknown_groups': len(delta), 'relation_on_relaxation': relation}
        if relation in CERTIFICATES:
            decisions.append((name, relation))
    require(len({decision for _, decision in decisions}) <= 1, 'incompatible anchor certificates')
    if not defined:
        result['decision'] = 'undefined_possible'
    elif decisions:
        result['anchor'], result['decision'] = decisions[0]
        result['decision_source'] = 'paired_ratio_envelope'
    else:
        lower, upper = lc['lower'] - rc['upper'], lc['upper'] - rc['lower']
        relation = reference.relation(lower, upper)
        if relation in CERTIFICATES:
            result['decision'] = relation
            result['decision_source'] = 'separate_conditional_intervals'
            result['separate_interval'] = [lower, upper]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'a fresh receiving record is required')
    root, native = args.artifact.resolve(), args.native.resolve()
    method_dir = root / 'external-studies/sew_natural/comparison_costs'
    sys.path.insert(0, str(method_dir))
    reference = load_module('independent_reference', method_dir / 'independent.py')
    raw_receiver = load_module('independent_native_records', method_dir / 'verify_native.py')
    registry_bytes = args.registry.read_bytes()
    registry = json.loads(registry_bytes)
    top = json.loads((native / 'receipt.json').read_text())
    protocol = json.loads((native / 'protocol.json').read_text())
    setup = json.loads((native / 'common-registration.json').read_text())
    require(top['status'] == 'complete', 'incomplete native collection')
    require(digest(registry_bytes) == protocol['public_registry_sha256'] == setup['public_registry_sha256'], 'public registry changed')
    require(not top['cross_run_candidate_label_reuse'] and not protocol['cross_run_candidate_label_reuse'], 'candidate results cached across runs')
    require(top['candidate_observation_files_read_before_selection'] == 0, 'historical candidate labels were read')
    expected_runs = 24 if protocol['design'] == 'balanced_native_timing' else 4
    require(len(top['runs']) == len(protocol['run_order']) == expected_runs, 'wrong run matrix size')
    if expected_runs == 24:
        order_counts = Counter()
        for index, row in enumerate(protocol['run_order']):
            order_counts[(row['scope'], row['method'], 'first' if index % 2 == 0 else 'second')] += 1
        require(len(order_counts) == 8 and set(order_counts.values()) == {3}, 'within-case method order is unbalanced')
    rows, groups, contracts = registry['rows'], registry['groups'], {}
    for row in rows:
        require(not raw_receiver.FORBIDDEN & set(row), 'public row contains a candidate result')
        identity = {k: row[k] for k in ('reference_sha256', 'candidate_sha256', 'contract_sha256')}
        require(digest(canonical(identity)) == row['source_contract_sha256'], 'public row identity differs')
    actual_assets = {}
    for group, meta in groups.items():
        require(not raw_receiver.FORBIDDEN & set(meta), 'public group contains a candidate result')
        require(digest(canonical({k: meta[k] for k in ('reference_sha256', 'candidate_sha256', 'contract_sha256')})) == group,
                'public group identity differs')
        for file_key, checksum_key in [('source_file', 'candidate_sha256'), ('reference_file', 'reference_sha256'),
                                       ('reference_observation_file', 'reference_observation_sha256')]:
            content = bounded(root, meta[file_key]).read_bytes()
            require(digest(content) == meta[checksum_key], 'source or reference observation changed')
            actual_assets[meta[file_key]] = digest(content)
            if file_key == 'reference_observation_file':
                if meta[file_key].endswith('.gz'):
                    content = gzip.decompress(content)
                require(json.loads(content)['status'] == 'passed', 'reference suite is unqualified')
        content = bounded(root, meta['contract_file']).read_bytes()
        contract = json.loads(content)
        require(digest(canonical(contract)) == meta['contract_sha256'], 'contract changed')
        actual_assets[meta['contract_file']] = digest(content)
        contracts[group] = contract
    require(actual_assets == setup['asset_files_sha256'], 'public registration assets differ')
    for name, checksum in protocol['source_sha256'].items():
        filename = name if name.endswith('.py') else name + '.py'
        require(digest((native / 'implementation' / filename).read_bytes()) == checksum, 'executed-source snapshot changed')
    cache, summaries = {}, []
    records_received = prefixes_received = 0
    for planned, summary in zip(protocol['run_order'], top['runs']):
        require(all(summary[k] == v for k, v in planned.items()), 'run differs from planned order')
        folder = bounded(native, summary['directory'])
        record = json.loads((folder / 'receipt.json').read_text())
        require({k: v for k, v in record.items() if k != 'queries'} == summary, 'per-run record differs from aggregate')
        require(all(math.isfinite(x) and x >= 0 for x in record['phase_seconds'].values()), 'invalid phase duration')
        require(record['audit_total_seconds'] >= sum(record['phase_seconds'].values()), 'phase durations exceed total')
        require(abs(record['audit_total_seconds'] - sum(record['phase_seconds'].values()) - record['unallocated_loop_seconds']) < 1e-9,
                'loop duration accounting differs')
        left, right, denominator = reference.coefficients(rows, planned['dataset'], planned['left'], planned['right'])
        require(denominator == record['denominator'], 'workload denominator differs')
        admitted = {g: True for g in set(left) | set(right) if groups[g]['candidate_sha256'] == groups[g]['reference_sha256']}
        attempted = set(admitted)
        require(len(admitted) == record['initial_reference_groups'], 'reference admissions differ')
        trace = json.loads((folder / 'trace.json').read_text())
        require(len(trace) == len(record['queries']) + 1 == record['candidate_suite_queries'] + 1, 'native prefix coverage differs')
        history = hashlib.sha256(canonical(sorted(admitted.items())))
        case = tuple(planned[k] for k in ('dataset', 'left', 'right', 'method'))
        for step, snapshot in enumerate(trace):
            require(snapshot['step'] == step and snapshot['groups_admitted'] == len(admitted), 'prefix metadata differs')
            key = case, history.hexdigest()
            if key not in cache:
                expected = (independent_paired(left, right, admitted, reference) if planned['method'] == 'paired'
                            else reference.bounds(left, right, admitted, 'independent', 'C'))
                select_method = 'coupled' if planned['method'] == 'paired' else 'independent'
                if planned['method'] == 'paired' and protocol.get('paired_selection_rule') == 'singleton_interval_minimax_else_differences':
                    intervals = [reference.conditional_bounds(model)
                                 for model in reference.compact_pair(left, right, admitted)]
                    if any(value['defined_for_some_completion'] and value['lower'] == value['upper']
                           for value in intervals):
                        select_method = 'independent'
                selected = (reference.next_query(left, right, admitted, attempted, select_method, 'C')
                            if expected['decision'] not in CERTIFICATES else None)
                cache[key] = expected, selected
            expected, selected = cache[key]
            require(snapshot['bounds'] == serial(expected), 'independent exact certificate reconstruction differs')
            prefixes_received += 1
            if step == len(record['queries']):
                require(expected['decision'] in CERTIFICATES and expected['decision'] == record['decision'], 'no final certificate')
                require(record['final_certificate'] == serial(expected), 'final certificate differs from received evidence')
                break
            require(expected['decision'] not in CERTIFICATES, 'native query follows an earlier certificate')
            query = record['queries'][step]
            require(query['step'] == step + 1 and query['group'] == selected and selected not in attempted,
                    'query selection differs from public coefficient and disclosed-history policy')
            content = bounded(native, query['evidence_file']).read_bytes()
            require(digest(content) == query['evidence_sha256'], 'native stdout record changed')
            evidence = json.loads(content)
            require(evidence['group'] == selected and evidence['source_sha256'] == groups[selected]['candidate_sha256']
                    and evidence['contract_sha256'] == groups[selected]['contract_sha256'], 'wrong execution binding')
            contract = contracts[selected]
            original = contract.get('native_contract', contract.get('original_native_contract', contract))
            tests = len(original['test_list']) if planned['dataset'] == 'mbpp_sanitized' else None
            label = raw_receiver.native_record(evidence['stdout'], planned['dataset'], tests,
                                               evidence['returncode'], evidence['interruption'])
            require(label is query['received_label'] and label is evidence['received_label'], 'new stdout does not support admitted label')
            attempted.add(selected)
            if label is not None:
                admitted[selected] = label
            history.update(canonical((selected, label)))
            records_received += 1
        summaries.append({'directory': summary['directory'], 'queries_received': len(record['queries']),
                          'first_certificate': record['decision']})
    require(records_received == top['total_candidate_suites'], 'native suite total differs')
    result = {'status': 'pass', 'runs_received': len(summaries), 'candidate_suite_records_received': records_received,
              'prefixes_received': prefixes_received, 'distinct_arithmetic_histories': len(cache),
              'historical_candidate_observations_read': 0,
              'source_snapshots_received': len(protocol['source_sha256']),
              'scope': 'Every fresh stdout, source/contract binding, public policy choice, prefix certificate and first stopping point independently received. Reference Fraction models and per-group calculations do not import producer certificate or state implementations.',
              'runs': summaries}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'runs'}, indent=2))


if __name__ == '__main__':
    main()
