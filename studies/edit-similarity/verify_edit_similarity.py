"""Independent verifier for the edit-similarity study.  Stdlib only.

1. Recomputes every unit from the raw sources (re-reads CREST/SEW rows and source files,
   re-derives labels and exclusions, checks hashes, recomputes the seven metrics) and
   compares with records.csv byte-for-byte per field.
2. Recomputes every summary number from records.csv with its own rank-based AUROC
   (no import of roc_auc), its own medians/quantiles and the same seeded cluster bootstrap.
Exits 1 on any mismatch; prints PASS otherwise.

    python3 -B -S studies/edit-similarity/verify_edit_similarity.py --out results/edit-similarity
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

warnings.filterwarnings('ignore', category=SyntaxWarning)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from covewm.metrics import source_metrics  # noqa: E402  (the fixed instrument)

NAMES = ('character', 'token', 'identifier_normalized', 'ast_type',
         'control_profile', 'identifier_multiset', 'identifier_style')
GROUPS = {
    'crest_reference': ['crest_reference'], 'crest_gpt4o': ['crest_gpt4o'], 'crest_qwen': ['crest_qwen'],
    'crest_pooled': ['crest_reference', 'crest_gpt4o', 'crest_qwen'],
    'sew_humaneval': ['sew_humaneval'], 'sew_mbpp': ['sew_mbpp'], 'sew': ['sew_humaneval', 'sew_mbpp'],
}
FAILURES = []


def fail(message):
    FAILURES.append(message)


def same(a, b, where):
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None or abs(a - b) > 1e-12:
            fail('%s: %r != %r' % (where, a, b))
    elif a != b:
        fail('%s: %r != %r' % (where, a, b))


def digest(data):
    return hashlib.sha256(data).hexdigest()


# ---------- part 1: raw recomputation

def receipt(rec):
    """Behavior label of a native receipt (same rule as the regression suite)."""
    if rec.get('evidence_rejected') or rec.get('interruption') or rec.get('returncode') != 0:
        value = None
    else:
        try:
            worker = json.loads(rec['stdout'])
        except json.JSONDecodeError:
            value = events_label([json.loads(s) for s in rec['stdout'].splitlines() if s.strip()],
                                 len(rec['execution_request']['test_list']), rec['returncode'])
        else:
            value = {'passed': True, 'failed': False}.get(worker['status'])
            if worker['status'] not in ('passed', 'failed', 'unknown', 'unavailable'):
                raise KeyError(worker['status'])
            if value is True and (worker.get('error') is not None or worker.get('check_finished', True) is not True):
                raise SystemExit('FAIL: contradictory suite success')
    if value is not rec['label']:
        raise SystemExit('FAIL: receipt label differs from declared label')
    return value


def events_label(events, n, returncode):
    if any(e['status'] == 'evidence_rejected' for e in events):
        raise SystemExit('FAIL: rejected evidence')
    bad = [e for e in events if e['event'] in ('source_compile', 'test_result') and e['status'] == 'failed']
    if bad:
        for e in bad:
            if e['error']['type'].rsplit('.', 1)[-1] in ('MemoryError', 'KeyboardInterrupt') or \
                    e['error']['phase'] not in ('compile_source', 'initialize_source', 'original_assertion'):
                raise SystemExit('FAIL: non-program failure admitted')
        return False
    done = [e for e in events if e['event'] == 'complete']
    tests = [e for e in events if e['event'] == 'test_result']
    comp = [e for e in events if e['event'] == 'source_compile']
    ok = (len(done) == 1 and done[0]['status'] == 'passed' and done[0]['scheduled_tests'] == n
          and done[0]['completed_tests'] == n and done[0]['passed_tests'] == n
          and len(comp) == 1 and comp[0]['status'] == 'passed' and len(tests) == n
          and sorted(e['test_index'] for e in tests) == list(range(n))
          and all(e['status'] == 'passed' and e['assertion_reached'] for e in tests) and returncode == 0)
    return True if ok else None


def unit(population, dataset, task, variant, ref_path, cand_path, rb, cb, bad):
    m = source_metrics(rb.decode('utf-8'), cb.decode('utf-8'), 'python')
    short = 'HumanEval' if dataset.lower().startswith('humaneval') else 'MBPP'
    row = [population, dataset, str(task), short + ':' + str(task).split('/')[-1], variant,
           ref_path.relative_to(ROOT).as_posix(), cand_path.relative_to(ROOT).as_posix(),
           digest(rb), digest(cb), 'contradicted' if bad else 'supported', str(int(bad)), str(int(rb == cb))]
    return row + [repr(1.0 - m[n + '_similarity']) for n in NAMES]


def raw_units():
    out, counts, excl = [], defaultdict(Counter), defaultdict(Counter)
    for cohort in ('reference', 'gpt4o', 'qwen'):
        pop = 'crest_' + cohort
        base = (ROOT / 'studies/crest/accepted' / cohort).resolve()
        for row in json.loads((base / 'results.json').read_bytes()):
            counts[pop]['rows'] += 1
            if row.get('emission'):
                em = row['emission']
            elif row.get('candidate_source') and row['embedding']['status'] == 'completed':
                em = 'emitted'
            elif row['embedding']['status'] == 'error' and not row.get('candidate_source'):
                em = 'rejected'
            else:
                em = 'unknown'
            counts[pop]['emitted' if em == 'emitted' else 'not_emitted_' + em] += 1
            ref_ok = receipt(row['reference_native'])
            cand = receipt(row['candidate_native']) if em == 'emitted' else None
            if em == 'emitted':
                counts[pop]['emitted_labeled' if cand is not None else 'emitted_label_unavailable'] += 1
            if ref_ok is not True:
                excl[pop]['reference_not_qualified_' + ('unavailable' if ref_ok is None else 'failed')] += 1
                continue
            counts[pop]['qualified'] += 1
            if em != 'emitted':
                excl[pop]['not_emitted_' + em] += 1
                continue
            if cand is None:
                excl[pop]['candidate_label_unavailable'] += 1
                continue
            rp, cp = base / row['reference_source'], base / row['candidate_source']
            rb, cb = rp.read_bytes(), cp.read_bytes()
            if not row['reference_native']['execution_request']['source'].endswith(rb.decode('utf-8')) or \
                    not row['candidate_native']['execution_request']['source'].endswith(cb.decode('utf-8')):
                raise SystemExit('FAIL: CREST source file is not the executed program')
            out.append(unit(pop, row['dataset'], row['task_id'], cohort, rp, cp, rb, cb, cand is False))
    he = (ROOT / 'results/sew/humaneval').resolve()
    mb = (ROOT / 'results/sew/mbpp').resolve()
    he_refs = {r['task_id']: r for r in json.loads((he / 'references.json').read_bytes())}
    sources = [('sew_humaneval', he, json.loads((he / 'rows.json').read_bytes()),
                lambda r: he_refs[r['task_id']]['source_path']),
               ('sew_mbpp', mb, json.loads((mb / 'factors/normalized_rows.json').read_bytes()),
                lambda r: r['reference_path'])]
    for pop, base, rows, refpath in sources:
        for row in rows:
            counts[pop]['rows'] += 1
            counts[pop]['emitted'] += 1
            v = row['validity_label']
            bad = {'supported': False, 'contradicted': True}.get(v) if isinstance(v, str) else (
                {1: False, 0: True}.get(v) if type(v) is int else None)
            counts[pop]['emitted_labeled' if bad is not None else 'emitted_label_unavailable'] += 1
            if row['reference_status'] != 'passed':
                excl[pop]['reference_not_qualified_' + str(row['reference_status'])] += 1
                continue
            counts[pop]['qualified'] += 1
            if bad is None:
                excl[pop]['candidate_label_unavailable'] += 1
                continue
            rp, cp = base / refpath(row), base / row['source_path']
            rb, cb = rp.read_bytes(), cp.read_bytes()
            if digest(rb) != row['reference_sha256'] or digest(cb) != row['candidate_sha256']:
                raise SystemExit('FAIL: SEW source hash mismatch %s' % cp)
            if pop == 'sew_humaneval' and he_refs[row['task_id']]['reference_sha256'] != row['reference_sha256']:
                raise SystemExit('FAIL: references.json hash mismatch')
            out.append(unit(pop, row['dataset'], row['task_id'], row['variant'] + '/' + row['key_id'],
                            rp, cp, rb, cb, bad))
    return out, counts, excl


# ---------- part 2: statistics from records.csv

def auc_rank(labels, scores):
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        mid = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = mid
        i = j + 1
    pos = sum(labels)
    neg = len(labels) - pos
    r = sum(rank for rank, y in zip(ranks, labels) if y == 1)
    return (r - pos * (pos + 1) / 2) / (pos * neg)


def pct(values, p):
    s = sorted(values)
    h = p * (len(s) - 1)
    lo = int(h)
    hi = lo + 1 if lo + 1 < len(s) else lo
    return s[lo] + (s[hi] - s[lo]) * (h - lo)


def med(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def label_of(auc):
    if auc is None:
        return None
    return ('distortion is associated with invalidity' if auc > 0.6 else
            'inverse association' if auc < 0.4 else 'distortion does not separate validity')


def check_population(name, rows, saved):
    y = [int(r['invalid']) for r in rows]
    d = {n: [float(r[n + '_distortion']) for r in rows] for n in NAMES}
    valid = [i for i, v in enumerate(y) if v == 0]
    bad = [i for i, v in enumerate(y) if v == 1]
    same(len(rows), saved['n_units'], name + '.n_units')
    same(len(valid), saved['n_valid'], name + '.n_valid')
    same(len(bad), saved['n_invalid'], name + '.n_invalid')
    same(sum(int(r['identical']) for r in rows), saved['n_identical'], name + '.n_identical')
    same(sum(int(rows[i]['identical']) for i in bad), saved['n_identical_invalid'], name + '.n_identical_invalid')
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r['cluster']].append(i)
    keys = sorted(groups)
    same(len(keys), saved['n_task_clusters'], name + '.n_task_clusters')
    same(len({rows[i]['cluster'] for i in bad}), saved['n_invalid_task_clusters'], name + '.n_invalid_clusters')
    rng = random.Random(20261125)
    boot = {n: [] for n in NAMES}
    skipped = 0
    for _ in range(2000):
        idx = []
        for _ in range(len(keys)):
            idx.extend(groups[rng.choice(keys)])
        ys = [y[i] for i in idx]
        if all(ys) or not any(ys):
            skipped += 1
            continue
        for n in NAMES:
            boot[n].append(auc_rank(ys, [d[n][i] for i in idx]))
    same(skipped, saved['bootstrap']['skipped_replicates'], name + '.skipped')
    same(2000 - skipped, saved['bootstrap']['used_replicates'], name + '.used')
    for n in NAMES:
        s = saved['instruments'][n]
        v = [d[n][i] for i in valid]
        x = [d[n][i] for i in bad]
        auc = auc_rank(y, d[n]) if v and x else None
        same(auc, s['auroc'], '%s.%s.auroc' % (name, n))
        ci = [pct(boot[n], 0.025), pct(boot[n], 0.975)] if boot[n] else None
        if (ci is None) != (s['auroc_ci95'] is None):
            fail('%s.%s.ci presence' % (name, n))
        elif ci:
            same(ci[0], s['auroc_ci95'][0], '%s.%s.ci_low' % (name, n))
            same(ci[1], s['auroc_ci95'][1], '%s.%s.ci_high' % (name, n))
        mv = med(v) if v else None
        same(mv, s['median_distortion_valid'], '%s.%s.median_valid' % (name, n))
        same(med(x) if x else None, s['median_distortion_invalid'], '%s.%s.median_invalid' % (name, n))
        frac = sum(t <= mv for t in x) / len(x) if x and v else None
        same(frac, s['fraction_invalid_at_or_below_valid_median'], '%s.%s.fraction' % (name, n))
        same(label_of(auc), s['interpretation'], '%s.%s.interpretation' % (name, n))
    cv, ci_ = d['character'], d['character']
    cv = [d['character'][i] for i in valid]
    ci_ = [d['character'][i] for i in bad]
    p10 = pct(cv, 0.10) if cv else None
    p90 = pct(ci_, 0.90) if ci_ else None
    c = saved['controlled_claim_comparison']
    same(p10, c['valid_character_distortion_p10'], name + '.p10')
    same(p90, c['invalid_character_distortion_p90'], name + '.p90')
    same(sum(t < p10 for t in ci_) if p10 is not None else None, c['small_faulty_edits'], name + '.small_faulty')
    same(sum(t > p90 for t in cv) if p90 is not None else None, c['large_harmless_edits'], name + '.large_harmless')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='results/edit-similarity')
    args = ap.parse_args()
    out = Path(args.out) if Path(args.out).is_absolute() else ROOT / args.out
    summary = json.loads((out / 'summary.json').read_bytes())
    protocol_path = ROOT / 'studies/edit-similarity/protocol.json'
    protocol = json.loads(protocol_path.read_bytes())
    same(protocol['status'], 'PRE_DECLARED', 'protocol.status')
    same(digest(protocol_path.read_bytes()), summary['protocol_sha256'], 'protocol_sha256')
    same(protocol['declared_at_utc'], summary['protocol_declared_at_utc'], 'protocol_declared_at_utc')
    for path, value in summary['input_sha256'].items():
        same(digest((ROOT / path).read_bytes()), value, 'input ' + path)
    csv_bytes = (out / 'records.csv').read_bytes()
    same(digest(csv_bytes), summary['records_csv_sha256'], 'records_csv_sha256')
    table = list(csv.reader(csv_bytes.decode('utf-8').splitlines()))
    header, body = table[0], table[1:]

    fresh, counts, excl = raw_units()
    same(len(fresh), len(body), 'record count')
    same(len(body), summary['records'], 'summary.records')
    for k, (a, b) in enumerate(zip(fresh, body)):
        if a != b:
            fail('records.csv row %d differs from raw recomputation' % (k + 1))
            if len(FAILURES) > 20:
                break
    rows = [dict(zip(header, r)) for r in body]
    for name, members in GROUPS.items():
        saved = summary['populations'][name]
        c, e = Counter(), Counter()
        for m in members:
            c.update(counts[m])
            e.update(excl[m])
        same(dict(sorted(c.items())), saved['counts'], name + '.counts')
        same(dict(sorted(e.items())), saved['excluded_by_reason'], name + '.excluded')
        check_population(name, [r for r in rows if r['population'] in members], saved)
    if FAILURES:
        for f in FAILURES[:50]:
            print('MISMATCH', f)
        print('FAIL (%d mismatches)' % len(FAILURES))
        sys.exit(1)
    print('records', len(body), 'populations', len(GROUPS), 'protocol', summary['protocol_sha256'])
    print('PASS')


if __name__ == '__main__':
    main()
