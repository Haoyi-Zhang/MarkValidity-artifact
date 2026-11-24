#!/usr/bin/env python3
"""Replay the upstream S1 rule and inspect source-binding controls.

This is a rule-level diagnostic. It does not alter the stock pipeline or count
its isolated rule outputs as any of the 102 stock embedding configurations.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

from verify_study import native

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ARTIFACT / 'results/revision-sew-aliasing')
    parser.add_argument('--binding-csv', type=Path, help='Derived table; defaults to RESULTS/binding-controls.csv.')
    args = parser.parse_args()
    results = args.results.resolve()
    upstream = json.loads((HERE / 'upstream.json').read_text())
    for rel, expected in upstream['files_sha256'].items():
        require(sha((HERE / 'vendor' / rel).read_bytes()) == expected, 'Upstream hash: ' + rel)
    sys.path.insert(0, str(HERE / 'vendor'))
    from sew.rules.base import parse, apply_edits
    from sew.rules.python_rules import S1CompoundAssign

    spec_bytes = (HERE / 'study-spec.json').read_bytes()
    spec = json.loads(spec_bytes)
    domain = spec['input_domain']
    diagnostics = []
    rule = S1CompoundAssign()
    for case in spec['cases']:
        tree, source = parse(case['source'], 'python')
        require(tree is not None, 'Reference must parse.')
        sites = list(rule.match(tree, source))
        require(len(sites) == 1, 'Expected exactly one S1 site: ' + case['case_id'])
        site = sites[0]
        guard = rule.guard(site, tree, source)
        require(guard, 'This diagnostic requires the actual upstream guard to admit the site.')
        target = 1 - site.variant
        edits = rule.write(site, source, target)
        changed = apply_edits(source, edits)
        before = native(source.decode(), domain)
        after = native(changed.decode(), domain)
        mismatches = [
            {'input': left['input'], 'reference': left['observation'], 'candidate': right['observation']}
            for left, right in zip(before, after) if left['observation'] != right['observation']
        ]
        require(len(mismatches) == (32 if case['kind'] == 'aliased_list' else 0), 'Unexpected rule result.')
        diagnostics.append({
            'case_id': case['case_id'], 'guard_admitted': guard,
            'site_span': list(site.span), 'source_variant': site.variant, 'target_variant': target,
            'reference_source': source.decode(), 'candidate_source': changed.decode(),
            'reference_sha256': sha(source), 'candidate_sha256': sha(changed),
            'edits': [{'start': e.start, 'end': e.end, 'new': e.new.decode()} for e in edits],
            'reference_observations': before, 'candidate_observations': after,
            'behavior_valid': not mismatches, 'mismatch_count': len(mismatches),
            'first_mismatch': mismatches[0] if mismatches else None,
        })
    rows = json.loads((results / 'rows.json').read_text())
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['candidate_sha256']].append(row)
    binding_controls = []
    for candidate_hash, group in sorted(grouped.items()):
        if len({row['behavior_valid'] for row in group}) < 2:
            continue
        for row in group:
            require(sha((results / row['candidate_path']).read_bytes()) == candidate_hash, 'Candidate hash mismatch.')
        binding_controls.append({
            'candidate_sha256': candidate_hash,
            'records': [{
                'case_id': row['case_id'], 'key_id': row['key_id'],
                'reference_sha256': row['reference_sha256'],
                'reference_path': row['reference_path'],
                'candidate_path': row['candidate_path'],
                'domain_sha256': row['domain_sha256'],
                'behavior_valid': row['behavior_valid'], 'detected': row['detected'],
                'first_mismatch': row['first_mismatch'],
            } for row in group],
        })
    require(len(binding_controls) == 13, 'Unexpected binding-control group count.')
    conflicting_hashes = {group['candidate_sha256'] for group in binding_controls}
    csv_path = args.binding_csv or results / 'binding-controls.csv'
    csv_fields = ['candidate_sha256', 'case_id', 'key_id', 'key_hex', 'reference_path', 'reference_sha256', 'candidate_path', 'domain_sha256', 'behavior_valid', 'detected', 'joint_success']
    csv_rows = [{key: row[key] for key in csv_fields} for row in rows if row['candidate_sha256'] in conflicting_hashes]
    with csv_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(csv_rows)
    default_rows = [r for r in rows if r['key_id'] == 'upstream_default' and r['kind'] == 'aliased_list']
    require(len(default_rows) == 2, 'Missing default-key pair.')
    require(len({r['candidate_sha256'] for r in default_rows}) == 1, 'Default-key candidates differ.')
    require(len({r['behavior_valid'] for r in default_rows}) == 2, 'Default-key obligations should differ.')
    require(default_rows[0]['detector_after'] == default_rows[1]['detector_after'], 'Default-key detector differs.')
    report = {
        'status': 'PASS', 'diagnostic_sha256': sha(Path(__file__).read_bytes()),
        'study_spec_sha256': sha(spec_bytes), 'rows_sha256': sha((results / 'rows.json').read_bytes()),
        'upstream_commit': upstream['commit'],
        'scope': 'Direct calls to unmodified upstream S1 match/guard/write; a rule-level diagnostic, not a stock-pipeline ablation.',
        'pipeline_allowlist': 'The retained discover(src, language) API has no public rule allowlist. No monkeypatch or registry edit was used.',
        'rule_id': 'S1',
        'rule_source': 'vendor/sew/rules/python_rules.py',
        'rule_source_sha256': upstream['files_sha256']['sew/rules/python_rules.py'],
        'rule_explanation': 'A numeric literal on the right bypasses numeric-type inference for the left variable. The admitted list multiplication forms differ in whether aliases observe in-place mutation.',
        'diagnostic_native_source_runs': 12,
        'diagnostic_native_input_evaluations': 12 * len(domain),
        'excluded_from_stock_grid_counts': True,
        'rule_diagnostics': diagnostics,
        'candidate_hash_groups_with_opposite_validity': len(binding_controls),
        'binding_control_csv_records': len(csv_rows),
        'binding_control_csv_sha256': sha(csv_path.read_bytes()),
        'binding_control_explanation': 'These retained stock outputs are byte-identical within each group, but their validity obligations use different reference programs. A candidate digest alone cannot identify the obligation.',
        'binding_controls': binding_controls,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
