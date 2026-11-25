"""Edit-similarity study: does source distortion separate invalid real watermark edits?

Pre-declared protocol: studies/edit-similarity/protocol.json (read and hashed here).
Stdlib only.  Run from the artifact root:

    python3 -B -S studies/edit-similarity/run_edit_similarity.py --out results/edit-similarity
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
import sys
import warnings
from collections import Counter
from pathlib import Path

# ast.parse of archived sources emits SyntaxWarning for invalid escapes; silence stderr noise only.
warnings.filterwarnings('ignore', category=SyntaxWarning)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from covewm.metrics import roc_auc, source_metrics  # noqa: E402

PROTOCOL = ROOT / 'studies/edit-similarity/protocol.json'
CREST = ROOT / 'studies/crest/accepted'
SEW_HE = ROOT / 'results/sew/humaneval'
SEW_MBPP = ROOT / 'results/sew/mbpp'
COHORTS = ('reference', 'gpt4o', 'qwen')
INSTRUMENTS = ('character', 'token', 'identifier_normalized', 'ast_type',
               'control_profile', 'identifier_multiset', 'identifier_style')
SEED = 20261125
REPLICATES = 2000
FIELDS = (['population', 'dataset', 'task_id', 'cluster', 'variant_key',
           'reference_path', 'candidate_path', 'reference_sha256', 'candidate_sha256',
           'label', 'invalid', 'identical']
          + [name + '_distortion' for name in INSTRUMENTS])
POPULATIONS = {
    'crest_reference': ('crest_reference',),
    'crest_gpt4o': ('crest_gpt4o',),
    'crest_qwen': ('crest_qwen',),
    'crest_pooled': ('crest_reference', 'crest_gpt4o', 'crest_qwen'),
    'sew_humaneval': ('sew_humaneval',),
    'sew_mbpp': ('sew_mbpp',),
    'sew': ('sew_humaneval', 'sew_mbpp'),
}


class Abort(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


# ---- label logic copied from regressions/test_natural_reporting.py and
# ---- regressions/test_publication_reporting.py (not imported)

def require(condition, message):
    if not condition:
        raise Abort(message)


def mbpp_observed_label(observation, expected_entries):
    events = observation['events']
    require(not any(e['status'] == 'evidence_rejected' for e in events),
            'Rejected evidence cannot enter the primary comparison')
    failures = [e for e in events if e['event'] in ('source_compile', 'test_result')
                and e['status'] == 'failed']
    if failures:
        for event in failures:
            error = event['error']
            require(error['type'].rsplit('.', 1)[-1] not in ('MemoryError', 'KeyboardInterrupt'),
                    'Resource error was admitted as a program contradiction')
            require(error['phase'] in ('compile_source', 'initialize_source', 'original_assertion'),
                    'Observer/test-infrastructure error was admitted as invalidity')
        return 0
    completed = [e for e in events if e['event'] == 'complete']
    tests = [e for e in events if e['event'] == 'test_result']
    compilation = [e for e in events if e['event'] == 'source_compile']
    complete = (len(completed) == 1 and completed[0]['status'] == 'passed'
                and completed[0]['scheduled_tests'] == expected_entries
                and completed[0]['completed_tests'] == expected_entries
                and completed[0]['passed_tests'] == expected_entries
                and len(compilation) == 1 and compilation[0]['status'] == 'passed'
                and len(tests) == expected_entries
                and sorted(e['test_index'] for e in tests) == list(range(expected_entries))
                and all(e['status'] == 'passed' and e['assertion_reached'] for e in tests)
                and observation['returncode'] == 0)
    return 1 if complete else None


def label(record):
    if record.get('evidence_rejected') or record.get('interruption') or record.get('returncode') != 0:
        actual = None
    else:
        try:
            worker = json.loads(record['stdout'])
        except json.JSONDecodeError:
            events = [json.loads(line) for line in record['stdout'].splitlines() if line.strip()]
            value = mbpp_observed_label({'events': events, 'returncode': record['returncode']},
                                        len(record['execution_request']['test_list']))
            actual = None if value is None else bool(value)
        else:
            actual = {'passed': True, 'failed': False, 'unknown': None,
                      'unavailable': None}[worker['status']]
            if actual is True and (worker.get('error') is not None or worker.get('check_finished', True) is not True):
                raise Abort('Incomplete or contradictory suite success')
    if actual is not record['label']:
        raise Abort('Declared native label differs from the worker receipt')
    return actual


def emission(row):
    if row.get('emission'):
        return row['emission']
    if row.get('candidate_source') and row['embedding']['status'] == 'completed':
        return 'emitted'
    if row['embedding']['status'] == 'error' and not row.get('candidate_source'):
        return 'rejected'
    return 'unknown'


# ---- populations

def cluster_key(dataset: str, task_id) -> str:
    name = 'HumanEval' if dataset.lower().startswith('humaneval') else 'MBPP'
    return name + ':' + str(task_id).rsplit('/', 1)[-1]


def make_record(population, dataset, task_id, variant_key, ref_path, cand_path, ref_bytes, cand_bytes, invalid):
    reference = ref_bytes.decode('utf-8')
    candidate = cand_bytes.decode('utf-8')
    sims = source_metrics(reference, candidate, 'python')
    record = {
        'population': population, 'dataset': dataset, 'task_id': str(task_id),
        'cluster': cluster_key(dataset, task_id), 'variant_key': variant_key,
        'reference_path': rel(ref_path), 'candidate_path': rel(cand_path),
        'reference_sha256': sha256_bytes(ref_bytes), 'candidate_sha256': sha256_bytes(cand_bytes),
        'label': 'contradicted' if invalid else 'supported', 'invalid': int(invalid),
        'identical': int(ref_bytes == cand_bytes),
    }
    for name in INSTRUMENTS:
        record[name + '_distortion'] = 1.0 - sims[name + '_similarity']
    return record


def crest_population(cohort):
    folder = CREST / cohort
    rows = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    counts = Counter(rows=len(rows))
    excluded = Counter()
    records = []
    for row in rows:
        e = emission(row)
        counts['emitted' if e == 'emitted' else 'not_emitted_' + e] += 1
        before = label(row['reference_native'])
        if row.get('qualified_reference') is not None and row['qualified_reference'] is not (before is True):
            raise Abort('qualified_reference disagrees with the reference receipt: %s' % row['task_id'])
        after = label(row['candidate_native']) if e == 'emitted' else None
        if e == 'emitted':
            counts['emitted_labeled' if after is not None else 'emitted_label_unavailable'] += 1
        if before is not True:
            excluded['reference_not_qualified_' + ('failed' if before is False else 'unavailable')] += 1
            continue
        counts['qualified'] += 1
        if e != 'emitted':
            excluded['not_emitted_' + e] += 1
            continue
        if after is None:
            excluded['candidate_label_unavailable'] += 1
            continue
        ref_path = folder / row['reference_source']
        cand_path = folder / row['candidate_source']
        require(ref_path.is_file() and cand_path.is_file(), 'Missing CREST source: %s' % row['task_id'])
        ref_bytes, cand_bytes = ref_path.read_bytes(), cand_path.read_bytes()
        for data, native, what in ((ref_bytes, row['reference_native'], 'reference'),
                                   (cand_bytes, row['candidate_native'], 'candidate')):
            executed = native['execution_request']['source']
            require(executed.endswith(data.decode('utf-8')),
                    'CREST %s file is not the executed source: %s %s' % (what, cohort, row['task_id']))
        records.append(make_record('crest_' + cohort, row['dataset'], row['task_id'], cohort,
                                   ref_path, cand_path, ref_bytes, cand_bytes, after is False))
    return records, counts, excluded


def sew_label(row):
    value = row['validity_label']
    if value in ('supported', 1) and value is not True:
        return False
    if value in ('contradicted', 0) and value is not False:
        return True
    return None


def sew_population(name, rows, base, reference_for):
    counts = Counter(rows=len(rows))
    excluded = Counter()
    records = []
    for row in rows:
        counts['emitted'] += 1
        invalid = sew_label(row)
        counts['emitted_labeled' if invalid is not None else 'emitted_label_unavailable'] += 1
        if row['reference_status'] != 'passed':
            excluded['reference_not_qualified_' + str(row['reference_status'])] += 1
            continue
        counts['qualified'] += 1
        if invalid is None:
            excluded['candidate_label_unavailable'] += 1
            continue
        ref_path = base / reference_for(row)
        cand_path = base / row['source_path']
        ref_bytes, cand_bytes = ref_path.read_bytes(), cand_path.read_bytes()
        require(sha256_bytes(ref_bytes) == row['reference_sha256'], 'Reference hash mismatch: %s' % ref_path)
        require(sha256_bytes(cand_bytes) == row['candidate_sha256'], 'Candidate hash mismatch: %s' % cand_path)
        records.append(make_record(name, row['dataset'], row['task_id'], row['variant'] + '/' + row['key_id'],
                                   ref_path, cand_path, ref_bytes, cand_bytes, invalid))
    return records, counts, excluded


def sew_humaneval():
    rows = json.loads((SEW_HE / 'rows.json').read_text(encoding='utf-8'))
    refs = {}
    for ref in json.loads((SEW_HE / 'references.json').read_text(encoding='utf-8')):
        require(ref['task_id'] not in refs, 'Duplicate HumanEval reference')
        refs[ref['task_id']] = ref

    def reference_for(row):
        ref = refs[row['task_id']]
        require(ref['reference_sha256'] == row['reference_sha256'], 'references.json hash differs from row')
        return ref['source_path']
    return sew_population('sew_humaneval', rows, SEW_HE, reference_for)


def sew_mbpp():
    rows = json.loads((SEW_MBPP / 'factors/normalized_rows.json').read_text(encoding='utf-8'))
    return sew_population('sew_mbpp', rows, SEW_MBPP, lambda row: row['reference_path'])


# ---- statistics

def quantile(values, p):
    ordered = sorted(values)
    position = p * (len(ordered) - 1)
    low = math.floor(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def interpret(auc):
    if auc is None:
        return None
    if auc > 0.6:
        return 'distortion is associated with invalidity'
    if auc < 0.4:
        return 'inverse association'
    return 'distortion does not separate validity'


def population_statistics(records):
    valid = [r for r in records if r['invalid'] == 0]
    invalid = [r for r in records if r['invalid'] == 1]
    clusters = {}
    for index, r in enumerate(records):
        clusters.setdefault(r['cluster'], []).append(index)
    order = sorted(clusters)
    rng = random.Random(SEED)
    samples = {name: [] for name in INSTRUMENTS}
    skipped = 0
    for _ in range(REPLICATES):
        chosen = [rng.choice(order) for _ in range(len(order))]
        indices = [i for key in chosen for i in clusters[key]]
        labels = [records[i]['invalid'] for i in indices]
        if 0 not in labels or 1 not in labels:
            skipped += 1
            continue
        for name in INSTRUMENTS:
            samples[name].append(roc_auc(labels, [records[i][name + '_distortion'] for i in indices]))
    result = {
        'n_units': len(records), 'n_valid': len(valid), 'n_invalid': len(invalid),
        'n_identical': sum(r['identical'] for r in records),
        'n_identical_invalid': sum(r['identical'] for r in invalid),
        'n_task_clusters': len(order),
        'n_invalid_task_clusters': len({r['cluster'] for r in invalid}),
        'bootstrap': {'replicates': REPLICATES, 'seed': SEED, 'skipped_replicates': skipped,
                      'used_replicates': REPLICATES - skipped},
        'instruments': {},
    }
    for name in INSTRUMENTS:
        key = name + '_distortion'
        v = [r[key] for r in valid]
        x = [r[key] for r in invalid]
        both = bool(v) and bool(x)
        auc = roc_auc([r['invalid'] for r in records], [r[key] for r in records]) if both else None
        median_valid = statistics.median(v) if v else None
        result['instruments'][name] = {
            'auroc': auc,
            'auroc_ci95': [quantile(samples[name], 0.025), quantile(samples[name], 0.975)] if samples[name] else None,
            'median_distortion_valid': median_valid,
            'median_distortion_invalid': statistics.median(x) if x else None,
            'fraction_invalid_at_or_below_valid_median': (sum(1 for d in x if d <= median_valid) / len(x)) if x and v else None,
            'interpretation': interpret(auc),
        }
    cv = [r['character_distortion'] for r in valid]
    ci = [r['character_distortion'] for r in invalid]
    p10 = quantile(cv, 0.10) if cv else None
    p90 = quantile(ci, 0.90) if ci else None
    result['controlled_claim_comparison'] = {
        'valid_character_distortion_p10': p10,
        'invalid_character_distortion_p90': p90,
        'small_faulty_edits': sum(1 for d in ci if d < p10) if p10 is not None else None,
        'large_harmless_edits': sum(1 for d in cv if d > p90) if p90 is not None else None,
    }
    return result


EXPECTED = {
    'crest_reference': {'rows': 591, 'emitted': 589, 'n_invalid': 15},
    'crest_gpt4o': {'rows': 1138, 'qualified': 948, 'n_valid': 934, 'n_invalid': 14},
    'crest_qwen': {'rows': 1138, 'qualified': 826, 'n_valid': 761, 'n_invalid': 13, 'not_emitted_rejected': 52},
    'sew_humaneval': {'n_invalid': 0},
    'sew_mbpp': {'n_invalid': 6},
}


def format_value(value):
    return repr(value) if isinstance(value, float) else str(value)


def records_csv(records):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    for r in records:
        writer.writerow({k: format_value(r[k]) for k in FIELDS})
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results/edit-similarity')
    args = parser.parse_args()
    out = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    require(protocol['status'] == 'PRE_DECLARED', 'Protocol is not pre-declared')
    protocol_sha = sha256_file(PROTOCOL)

    parts = {}
    for cohort in COHORTS:
        parts['crest_' + cohort] = crest_population(cohort)
    parts['sew_humaneval'] = sew_humaneval()
    parts['sew_mbpp'] = sew_mbpp()

    records = [r for name in parts for r in parts[name][0]]
    out.mkdir(parents=True, exist_ok=True)
    text = records_csv(records)
    (out / 'records.csv').write_text(text, encoding='utf-8', newline='')

    populations = {}
    for name, members in POPULATIONS.items():
        selected = [r for r in records if r['population'] in members]
        counts, excluded = Counter(), Counter()
        for member in members:
            counts.update(parts[member][1])
            excluded.update(parts[member][2])
        stats = population_statistics(selected)
        populations[name] = {
            'members': list(members),
            'counts': dict(sorted(counts.items())),
            'excluded_by_reason': dict(sorted(excluded.items())),
            **stats,
        }
    checks = {}
    for name, expected in EXPECTED.items():
        observed = {**populations[name]['counts'], **populations[name]['excluded_by_reason'],
                    'n_valid': populations[name]['n_valid'], 'n_invalid': populations[name]['n_invalid']}
        checks[name] = {k: {'expected': v, 'observed': observed.get(k, 0), 'match': observed.get(k, 0) == v}
                        for k, v in expected.items()}
    mbpp_invalid = sorted({(r['task_id'], r['variant_key']) for r in records
                           if r['population'] == 'sew_mbpp' and r['invalid']})
    inputs = [CREST / c / 'results.json' for c in COHORTS] + [
        SEW_HE / 'rows.json', SEW_HE / 'references.json', SEW_MBPP / 'factors/normalized_rows.json',
        ROOT / 'src/covewm/metrics.py', Path(__file__).resolve()]
    summary = {
        'study': 'edit-similarity',
        'status': 'COMPLETE',
        'protocol': rel(PROTOCOL),
        'protocol_sha256': protocol_sha,
        'protocol_declared_at_utc': protocol['declared_at_utc'],
        'input_sha256': {rel(p): sha256_file(p) for p in inputs},
        'records_csv_sha256': sha256_bytes(text.encode('utf-8')),
        'records': len(records),
        'instruments': list(INSTRUMENTS),
        'expected_count_checks': checks,
        'sew_mbpp_invalid_units': [list(x) for x in mbpp_invalid],
        'populations': populations,
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='')
    print('records', len(records), 'protocol', protocol_sha)
    for name, pop in populations.items():
        print(name, pop['n_valid'], pop['n_invalid'],
              {k: v['auroc'] for k, v in pop['instruments'].items()})


if __name__ == '__main__':
    try:
        main()
    except Abort as error:
        print('ABORT:', error, file=sys.stderr)
        sys.exit(1)
