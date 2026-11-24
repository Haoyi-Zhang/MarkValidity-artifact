"""Compare all frozen MBPP v1/v2 sources, decisions and test observations.

Timing, traceback paths and new v2 admission counters are version diagnostics.
All source bytes, detector/embedding records, original per-test observations,
compile outcomes and primary pass/fail labels must remain identical here.
"""
import argparse
import hashlib
import json
from pathlib import Path

FACTORS = ('stock', 's1_literal_predecessor', 's4_return_boundary', 's1_s4')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def observed(result):
    events = []
    for event in result['events']:
        if event['event'] == 'complete':
            selected = {k: event[k] for k in ('event', 'status', 'scheduled_tests', 'completed_tests', 'passed_tests', 'failed_tests')}
        else:
            selected = {k: v for k, v in event.items() if k != 'elapsed_seconds'}
            if selected.get('error'):
                selected['error'] = {k: v for k, v in selected['error'].items() if k != 'traceback'}
        events.append(selected)
    return {'status': result['status'], 'returncode': result['returncode'], 'stderr': result['stderr'], 'events': events}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--v1-results', type=Path, required=True)
    parser.add_argument('--v2-results', type=Path, required=True)
    args = parser.parse_args()
    comparisons = []
    fields = ('task_id', 'key_id', 'key_hex', 'reference_sha256', 'candidate_sha256', 'source_changed',
              'reference_status', 'candidate_status', 'candidate_compile_status', 'candidate_suite_pass',
              'detected', 'validity_status', 'joint_supported', 'failed_test_indices', 'embedding', 'detector', 'reference_detector')
    for variant in FACTORS:
        before_dir = args.v1_results / 'factors' / variant
        after_dir = args.v2_results / 'factors' / variant
        before = json.loads((before_dir / 'rows.json').read_text())
        after = json.loads((after_dir / 'rows.json').read_text())
        require(len(before) == len(after) == 1281, 'Full factor is required')
        assertions = 0
        for a, b in zip(before, after):
            require({k:a.get(k) for k in fields} == {k:b.get(k) for k in fields}, 'Source/method/outcome differs')
            require((before_dir / a['candidate_path']).read_bytes() == (after_dir / b['candidate_path']).read_bytes(), 'Candidate bytes differ')
            old = json.loads((before_dir / a['observations_path']).read_text())
            new = json.loads((after_dir / b['observations_path']).read_text())
            require(observed(old) == observed(new), 'A primary per-test observation differs')
            require(b['evidence_admission'] == 'accepted', 'Primary v2 evidence was not admitted')
            assertions += sum(e['event'] == 'test_result' for e in new['events'])
        refs_old = json.loads((before_dir / 'references.json').read_text())
        refs_new = json.loads((after_dir / 'references.json').read_text())
        require(len(refs_old) == len(refs_new) == 427, 'Full reference population is required')
        for a,b in zip(refs_old,refs_new):
            require(a['task_id'] == b['task_id'] and a['source_sha256'] == b['source_sha256'], 'Reference source identity differs')
            require((before_dir / a['source_path']).read_bytes() == (after_dir / b['source_path']).read_bytes(), 'Reference bytes differ')
            old = json.loads((before_dir / a['observation_path']).read_text())
            new = json.loads((after_dir / b['observation_path']).read_text())
            require(observed(old) == observed(new), 'A reference per-test observation differs')
            assertions += sum(e['event'] == 'test_result' for e in new['events'])
        comparisons.append({'variant': variant, 'reference_sources': len(refs_new), 'candidate_sources': len(after),
                            'original_test_observations': assertions,
                            'v1_rows_sha256': hashlib.sha256((before_dir / 'rows.json').read_bytes()).hexdigest(),
                            'v2_rows_sha256': hashlib.sha256((after_dir / 'rows.json').read_bytes()).hexdigest()})
    print(json.dumps({'status': 'PASS', 'scope': 'All frozen primary sources, embeddings, detector decisions and original-test observations; diagnostic time/traceback paths and explicit v2 admission metadata excluded.',
                      'comparisons': comparisons, 'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
