"""Reconstruct normalized numerical estimands from frozen raw MBPP factor rows."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', type=Path, required=True)
    args = parser.parse_args()
    folder = args.results_root.resolve() / 'factors'
    summary = json.loads((folder / 'comparison_summary.json').read_text())
    normalized = json.loads((folder / 'normalized_rows.json').read_text())
    provenance = json.loads((folder / 'normalization_provenance.json').read_text())
    for field, filename in [('normalized_rows_sha256', 'normalized_rows.json'),
                            ('groups_sha256', 'source_contract_groups.json'),
                            ('comparison_summary_sha256', 'comparison_summary.json')]:
        assert provenance[field] == sha((folder / filename).read_bytes()), filename
    checks = []
    for variant in summary['per_variant_all_attempts']:
        raw = json.loads((folder / variant / 'rows.json').read_text())
        joined = [r for r in normalized if r['variant'] == variant]
        assert len(raw) == len(joined) == 1281
        expected_rows = {(r['task_id'], r['key_id']): r for r in raw}
        for row in joined:
            original = expected_rows[(row['original_task_id'], row['key_id'])]
            assert row['detected'] == original['detected']
            assert row['validity_label'] == {'supported': 1, 'contradicted': 0, 'unavailable': None}[original['validity_status']]
            assert row['candidate_sha256'] == original['candidate_sha256']
            identity = {k:row[k] for k in ('reference_sha256','candidate_sha256','contract_sha256')}
            canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
            assert row['source_contract_sha256'] == sha(canonical)
            assert row['suite_cost'] == 1
        for population, selected in [('per_variant_all_attempts', raw),
                                     ('per_variant_reference_passing_subset', [r for r in raw if r['reference_status'] == 'passed'])]:
            n = len(selected)
            v = sum(r['validity_status'] == 'supported' for r in selected)
            d = sum(r['detected'] is True for r in selected)
            j = sum(r['validity_status'] == 'supported' and r['detected'] is True for r in selected)
            assert all(r['validity_status'] != 'unavailable' and r['detected'] is not None for r in selected)
            expected = {'attempts': n, 'valid': v, 'detected': d, 'joint': j,
                        'A': v/n, 'D': d/n, 'J': j/n, 'C': j/v if v else None}
            actual = summary[population][variant]
            for field, value in expected.items():
                assert actual[field] == value, (population, variant, field, actual[field], value)
            checks.append({'population': population, 'variant': variant, **expected})
    report = {'status': 'PASS', 'scope': 'Numerical estimands and normalized labels independently reconstructed from all frozen raw factor rows.',
              'definitions': {'A':'valid / attempts', 'D':'detected / attempts', 'J':'valid-and-detected / attempts',
                              'C':'valid-and-detected / valid; undefined if no valid outputs'},
              'checks': checks, 'normalized_rows_checked': len(normalized),
              'summary_sha256': sha((folder / 'comparison_summary.json').read_bytes()),
              'receiver_sha256': sha(Path(__file__).read_bytes())}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
