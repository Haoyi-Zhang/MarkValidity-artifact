#!/usr/bin/env python3
"""Portable independent receiving of the fixed natural-study claims.

Usage:
    python review_natural_claims.py --project /path/to/MarkValidity_TOSEM
    python review_natural_claims.py --project /path/to/MarkValidity_TOSEM --output receipt.json

This checker imports no producer, normalizer, selector, or bound routine. It reads
frozen ledgers and retained receipts, recomputes the representative arithmetic,
and performs no candidate execution. JSON goes to stdout by default; --output
exclusively creates a new receipt. Historical manual annotations are explicitly
separate from the automatic PASS and require human review when prose changes.
"""
import argparse
import collections
import sys
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics

parser = argparse.ArgumentParser(
    description="Independently receive the fixed natural-study claims without executing candidate programs.",
    epilog="The script checks arithmetic and retained-byte consistency. Historical manual notes are not a fresh human review.")
parser.add_argument('--project', type=Path, required=True,
                    help='Extracted project root containing artifact/ and paper/.')
parser.add_argument('--output', type=Path,
                    help='Write the JSON receipt to this new file; default prints the complete receipt to stdout.')
args = parser.parse_args()
if not __debug__:
    parser.error('Run without -O/-OO: validation assertions must be enabled.')
ROOT = args.project.resolve()
BASE = ROOT / 'artifact/results/revision-sew-natural'
OUT = args.output.resolve() if args.output else None
if not BASE.is_dir() or not (ROOT / 'paper').is_dir():
    parser.error('--project must contain artifact/results/revision-sew-natural and paper/.')
if OUT is not None and OUT.exists():
    parser.error('--output must name a new file; existing files are never overwritten.')
INPUT_HASHES = {}


def record_hash(path, digest):
    try:
        key = str(path.resolve().relative_to(ROOT))
    except ValueError:
        key = str(path.resolve())
    INPUT_HASHES[key] = digest
    return digest


def read(path):
    data = path.read_bytes()
    record_hash(path, hashlib.sha256(data).hexdigest())
    return json.loads(data)


def sha(path):
    return record_hash(path, hashlib.sha256(path.read_bytes()).hexdigest())


def v(row):
    value = row['validity_label']
    if value == 'supported' or value == 1:
        return 1
    if value == 'contradicted' or value == 0:
        return 0
    return None


def canonical_variant(row):
    return {'s1_literal_predecessor': 's1', 's4_return_boundary': 's4'}.get(row['variant'], row['variant'])


rows_he = read(BASE / 'humaneval/rows.json')
rows_mb = read(BASE / 'mbpp/factors/normalized_rows.json')
rows = rows_he + rows_mb
index = read(BASE / 'analysis-primary/group_index.json')
comparisons = read(BASE / 'analysis-primary/comparisons.json')
review = {
    'status': 'PASS',
    'scope': 'Automated independent arithmetic and retained-evidence consistency checks for the fixed natural study. No scientific programs are reexecuted and no new manual reading is performed.',
    'method': 'Rebuild workload coefficients from final normalized rows; independently compute exact Fraction single-score bounds and shared joint/common-remainder bounds at every prefix of the four main schedules. Check selected raw emitted source and all retained natural counterexample coordinates. Reconcile expanded results with the completed full read-only receiver and rerun comparison receipts.',
    'schema': 'markvalidity-independent-natural-claim-receiving-v1',
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'candidate_program_execution_performed': False,
    'fresh_manual_review_performed': False,
    'input_files_sha256': INPUT_HASHES,
    'outcomes': [],
    'variant_changes': [],
    'comparisons': [],
    'automated_check_failures': [],
}
bound_paths = [
    'artifact/results/revision-sew-natural/humaneval/rows.json',
    'artifact/results/revision-sew-natural/mbpp/factors/normalized_rows.json',
    'artifact/results/revision-sew-natural/enhanced-humaneval/rows.json',
    'artifact/results/revision-sew-natural/analysis-primary/comparisons.json',
    'artifact/results/revision-sew-natural/analysis-primary/group_index.json',
    'artifact/results/revision-sew-natural/analysis-primary/manifest.json',
    'artifact/results/revision-sew-natural/humaneval/receiving-current.json',
    'artifact/results/revision-sew-natural/native-audit/independent-receiving.json',
    'paper/main.tex', 'paper/figdata/natural-results.tex',
    'paper/figdata/natural-protocol.tex', 'paper/figdata/natural-macros.tex',
    'paper/figdata/natural-outcomes.tex', 'paper/figdata/natural-costs.tex',
    'paper/figdata/natural-enhanced-unknown.tex',
]
for relative in bound_paths:
    review['input_files_sha256'][relative] = sha(ROOT / relative)

assert len(rows) == 7092
assert len({r['source_contract_sha256'] for r in rows}) == 1893
assert all(r['suite_cost'] == 1 for r in rows)
assert all(v(r) is not None for r in rows)
for dataset, rr in [('HumanEval', rows_he), ('mbpp_sanitized', rows_mb)]:
    byvar = collections.defaultdict(list)
    for row in rr:
        byvar[canonical_variant(row)].append(row)
    for variant, batch in byvar.items():
        n = len(batch)
        validity = sum(v(r) for r in batch)
        detected = sum(r['detected'] for r in batch)
        joint = sum(v(r) * r['detected'] for r in batch)
        assert detected == joint
        review['outcomes'].append(dict(dataset=dataset, variant=variant, configurations=n,
                                       supported=validity, contradicted=n-validity,
                                       detected=detected, joint=joint,
                                       conditional=str(Fraction(joint, validity))))
    stock = {(r['task_id'], r['key_id']): r for r in byvar['stock']}
    for variant in ['s1', 's4', 's1_s4']:
        other = {(r['task_id'], r['key_id']): r for r in byvar[variant]}
        review['variant_changes'].append(dict(
            dataset=dataset, left='stock', right=variant,
            changed_candidate_sources=sum(stock[k]['candidate_sha256'] != other[k]['candidate_sha256'] for k in stock),
            detector_lost=sum(stock[k]['detected'] and not other[k]['detected'] for k in stock),
            detector_gained=sum(not stock[k]['detected'] and other[k]['detected'] for k in stock)))


def coeffs(dataset, left, right):
    subset = [r for r in rows if r['dataset'] == dataset and canonical_variant(r) in (left, right)]
    co = collections.defaultdict(lambda: [0, 0, 0, 0])
    labels = {}
    free = set()
    for r in subset:
        cid = r['source_contract_sha256']
        side = 0 if canonical_variant(r) == left else 2
        co[cid][side] += int(r['detected'])
        co[cid][side+1] += 1
        if cid in labels:
            assert labels[cid] == v(r)
        labels[cid] = v(r)
        if r['candidate_sha256'] == r['reference_sha256']:
            free.add(cid)
            assert v(r) == 1
    return subset, co, labels, free


def ratio_bounds(j0, b0, remaining):
    assert b0 > 0
    available = [(a, b) for a, b in remaining if b]
    order = sorted(available, key=lambda p: Fraction(p[0], p[1]))
    answer = []
    for direction in [order, list(reversed(order))]:
        j, b = j0, b0
        values = [Fraction(j, b)]
        for a, beta in direction:
            j += a
            b += beta
            values.append(Fraction(j, b))
        answer.append(values)
    return [min(answer[0]), max(answer[1])]


def decision(bounds):
    lo, hi = bounds
    if lo > 0:
        return 'left_strict'
    if hi < 0:
        return 'right_strict'
    if lo == hi == 0:
        return 'tie'
    return 'unresolved'


def snapshot(co, labels, known):
    jl = vl = jr = vr = 0
    remaining = []
    for cid, (a, b, c, d) in co.items():
        if cid in known:
            z = labels[cid]
            jl += z*a
            vl += z*b
            jr += z*c
            vr += z*d
        else:
            remaining.append((a, b, c, d))
    shared_j = [jl-jr+sum(min(0, a-c) for a,b,c,d in remaining),
                jl-jr+sum(max(0, a-c) for a,b,c,d in remaining)]
    separate_j = [jl-jr-sum(c for a,b,c,d in remaining),
                  jl-jr+sum(a for a,b,c,d in remaining)]
    l = ratio_bounds(jl, vl, [(a,b) for a,b,c,d in remaining])
    r = ratio_bounds(jr, vr, [(c,d) for a,b,c,d in remaining])
    separate_c = [l[0]-r[1], l[1]-r[0]]
    equal = all(a == c and b == d for a,b,c,d in remaining)
    if equal:
        terms = [(jl-jr)*b+(vr-vl)*a for a,b,c,d in remaining]
        margin = [jl*vr-jr*vl+sum(min(0,t) for t in terms),
                  jl*vr-jr*vl+sum(max(0,t) for t in terms)]
        shared_c = margin
    else:
        shared_c = separate_c
        margin = None
    return dict(coupled_J=shared_j, independent_J=separate_j,
                coupled_C=shared_c, independent_C=separate_c,
                left_C=l, right_C=r, known_mass=[jl,vl,jr,vr],
                common_remainder=equal, common_remainder_margin=margin)


def serial_snapshot(snap):
    return {k: [str(x) if isinstance(x, Fraction) else x for x in value]
            if isinstance(value, list) else value for k, value in snap.items()}


for case, dataset in [('humaneval__stock__s1', 'HumanEval'), ('mbpp__stock__s4', 'mbpp_sanitized')]:
    expected_case = comparisons[case]
    subset, co, labels, free = coeffs(dataset, expected_case['left'], expected_case['right'])
    n = len(subset)//2
    metadata = dict(case=case, denominator=n, groups=len(co), reference_identity_groups=len(free),
                    nonfree_unique=len(co)-len(free),
                    nonfree_rows=sum(r['source_contract_sha256'] not in free for r in subset),
                    influential_joint_groups=sum(a != c for cid,(a,b,c,d) in co.items() if cid not in free),
                    coefficient_different_groups=sum((a,b) != (c,d) for cid,(a,b,c,d) in co.items() if cid not in free))
    assert metadata['nonfree_unique'] == expected_case['full_unique_group_suites_after_reference']
    assert metadata['nonfree_rows'] == expected_case['full_row_suites_after_reference']
    assert metadata['influential_joint_groups'] == expected_case['J_gap_influential_groups']
    assert metadata['coefficient_different_groups'] == expected_case['C_coefficient_different_groups']
    metadata['schedules'] = []
    for policy, target in [('joint_width_per_suite', 'J'), ('conditional_differences_first', 'C')]:
        scheduled = expected_case['schedules'][policy]
        order = [index[i]['source_contract_sha256'] for i in scheduled['schedule']]
        assert len(order) == len(set(order)) == len(co)-len(free)
        assert set(order) | free == set(co)
        known = set(free)
        found = {}
        for step in range(len(order)+1):
            if step:
                known.add(order[step-1])
            snap = snapshot(co, labels, known)
            for name in [f'coupled_{target}', f'independent_{target}']:
                if name not in found and decision(snap[name]) != 'unresolved':
                    found[name] = dict(suite_queries=step, decision=decision(snap[name]), snapshot=serial_snapshot(snap))
            if len(found) == 2:
                break
        for name, actual in found.items():
            expected = scheduled['first_certificates'][name]
            assert actual['suite_queries'] == expected['suite_queries'], (case,policy,name,actual,expected)
            assert actual['decision'] == expected['decision']
            assert [str(x) for x in actual['snapshot'][name]] == [str(expected['snapshot'][name]['lower']), str(expected['snapshot'][name]['upper'])]
        metadata['schedules'].append(dict(policy=policy, target=target, checked_each_prefix_through=step, first_certificates=found))
    # Joint hash-order sensitivity is recomputed with integer coefficients only.
    hash_first = []
    for seed in range(16):
        sch = expected_case['schedules'][f'hash_{seed:02d}']
        order = [index[i]['source_contract_sha256'] for i in sch['schedule']]
        known = set(free)
        value = sum((co[k][0]-co[k][2])*labels[k] for k in known)
        lo = value + sum(min(0,a-c) for k,(a,b,c,d) in co.items() if k not in known)
        hi = value + sum(max(0,a-c) for k,(a,b,c,d) in co.items() if k not in known)
        step = 0
        while decision([lo,hi]) == 'unresolved':
            k = order[step]
            step += 1
            change = co[k][0]-co[k][2]
            lo += change*labels[k]-min(0,change)
            hi += change*labels[k]-max(0,change)
        assert step == sch['first_certificates']['coupled_J']['suite_queries']
        hash_first.append(step)
    metadata['independent_joint_hash_sensitivity'] = dict(first_suite_counts=hash_first, minimum=min(hash_first), maximum=max(hash_first), median=statistics.median(hash_first))
    review['comparisons'].append(metadata)

# The emitted listing includes exactly the two spaces produced by the S4 tree.
sources = {}
for variant, expected in [('stock', 'returnmax_length, max_list'), ('s4', 'return  max_length, max_list')]:
    row = next(r for r in rows_mb if canonical_variant(r)==variant and r['task_id']=='MBPP/290' and r['key_id']=='upstream_default')
    path = BASE / 'mbpp' / row['source_path']
    assert sha(path) == row['candidate_sha256']
    line = next(s.strip() for s in path.read_text().splitlines() if 'return' in s)
    assert line == expected
    sources[variant] = {'line':line, 'sha256':sha(path), 'source_path':row['source_path']}
reference_path = BASE / 'mbpp' / row['reference_path']
assert 'return(max_length, max_list)' in reference_path.read_text()
sources['reference'] = {'line':'return(max_length, max_list)', 'sha256':sha(reference_path)}
failed = [(r['task_id'],r['key_id'],canonical_variant(r),r['failed_test_indices']) for r in rows_mb if not v(r)]
assert len(failed) == 6
assert all(indices == [0,1,2] for task,key,var,indices in failed)
recheck = read(BASE / 'mbpp/factors/s4-independent-recheck/report.json')
assert (recheck['stock_assertion_failures'],recheck['s4_original_assertions_passed'],recheck['reference_original_assertions_passed']) == (9,9,9)
review['lexical_boundary'] = dict(exact_listing_sources=sources, failed_configurations=failed,
    independent_standalone_execution_counts={k:recheck[k] for k in ['configurations','unique_public_tasks','standalone_processes','stock_assertion_failures','s4_original_assertions_passed','reference_original_assertions_passed']})

receiver = read(BASE / 'humaneval/receiving-current.json')
assert receiver['status'] == 'PASS'
assert receiver['primary']['rows_sha256'] == sha(BASE / 'humaneval/rows.json')
assert receiver['enhanced']['rows_sha256'] == sha(BASE / 'enhanced-humaneval/rows.json')
enhanced = receiver['enhanced']
assert enhanced['recorded_input_pairs'] == 124253
assert enhanced['comparable_input_pairs'] == 124158
assert enhanced['unavailable_input_pairs'] == 95
assert enhanced['return_mismatches'] == enhanced['post_argument_mismatches'] == enhanced['stream_mismatches'] == 0
review['expanded_input'] = enhanced
comparison = read(BASE / 'enhanced-humaneval/v2-v3-observation-comparison.json')
review['expanded_v2_v3_comparison'] = comparison

boundary = read(BASE / 'observer-boundaries-v3-controls.json')
mb_controls = read(BASE / 'mbpp/supporting/observer-v2-controls/report.json')
assert boundary['status'] == mb_controls['status'] == 'PASS'
assert boundary['controls'] == 45 and all(r['passed'] for r in boundary['records'])
assert len(mb_controls['records']) == 14
review['observer_controls'] = dict(humaneval_primary=24, humaneval_expanded=21, mbpp=14,
    primary_cases=[r['control'] for r in boundary['records'] if r['family']=='primary'],
    expanded_cases=[r['control'] for r in boundary['records'] if r['family']=='enhanced'],
    mbpp_cases=[r['case'] for r in mb_controls['records']],
    note='Counts and retained control outcomes are checked automatically. The S14.4 wording assessment is a historical manual note below.')

registry = read(BASE / 'public-registry.json')
for r in registry['rows']:
    assert not any(k in r for k in ['validity_label','joint','candidate_status','observation_path','candidate_observation_path'])
for g in registry['groups'].values():
    assert not any(k in g for k in ['validity_label','joint','candidate_status','observation_file','candidate_observation_file'])
native = read(BASE / 'native-audit/independent-receiving.json')
assert native['status'] == 'PASS'
assert native['historical_candidate_labels_read'] == native['historical_candidate_observation_files_read'] == 0
native_cases = []
for case in native['cases']:
    directory = BASE / 'native-audit' / case['case']
    certificate = read(directory / 'certificate.json')
    trace = read(directory / 'trace.json')
    count = certificate['candidate_suite_queries']
    assert len(trace) == count+1
    assert trace[-1]['coupled_'+case['target']]['decision'] == certificate['decision']
    assert trace[-2]['coupled_'+case['target']]['decision'] == 'unresolved'
    native_cases.append({k:certificate[k] for k in ['case','target','candidate_suite_queries','decision']})
assert sum(c['candidate_suite_queries'] for c in native_cases) == 313
review['fresh_execution'] = dict(public_registry_has_no_candidate_labels_or_observation_paths=True,
    candidate_suites=313, cases=native_cases,
    independent_receiving_status=native['status'],
    independent_receiving_historical_candidate_labels_read=0,
    note='This reviewer inspects retained native traces and the independent fresh-file receiving receipt; it does not itself execute another 313 suites.')


# Fixed historical annotations, deliberately separate from automated checks.
retained_notes = {'provenance': 'Retained manual claim review from the revision round that produced '
               'final-science-review.json; copied into this portable checker without extending the '
               'original reading scope.',
 'fresh_manual_review_performed': False,
 'interpretation': 'These fixed notes document an earlier manual review. Re-running this checker '
                   'does not reread the prose, establish source entailment, or renew that manual '
                   'judgment. Text changes require human review.',
 'reviewed_text_sha256': {'paper/main.tex': '534b9eca4f7244ed77c75a82a70f5da6d31b7f214956d78b7bead47b13d08800',
                          'paper/figdata/natural-results.tex': '5558b668022c7e8f0247ab946552061ec998c9404588c273c2751885b5793bb1',
                          'paper/figdata/natural-protocol.tex': '8ad2f87927b7f7352800a4f407b96bcdcd01dae156077f6bd2ccdaa412b20b1c',
                          'paper/figdata/natural-macros.tex': '28041d430eb8b6c98e9ebdbbe3f525265807b1941fe878527eff7d2312dc5496',
                          'paper/figdata/natural-outcomes.tex': '134026a9f6d6650399a9708c19abe28f8e2fa7ca517b9568cef75f9c66d19fef',
                          'paper/figdata/natural-costs.tex': 'c04bdd24e61f383e2dc05a3588b6932f95682c989469a2d5c75a27bef617fa52',
                          'paper/figdata/natural-enhanced-unknown.tex': 'c655477bf68cb9cca4e5acf4a0b033a2048c9ccee14d4fc6f4505ab8ba7b5c6e'},
 'notes': [{'location': 'Results: emitted outputs',
            'status': 'supported',
            'finding': 'All natural cells have D=J. The manuscript retains the negative result and '
                       'does not use the natural failures as detected-invalid examples.'},
           {'location': 'Results: Listing natural-boundary',
            'status': 'supported',
            'finding': 'Exact reference, stock, and S4 source lines checked. S4 line contains two '
                       'spaces. Three affected configurations arise from two tasks; nine original '
                       'stock assertions fail. Other formatting changes within these three emitted '
                       'programs are not misrepresented as a single-byte whole-output difference.'},
           {'location': 'Results: S1 mechanism interpretation',
            'status': 'supported',
            'finding': 'Source changes and detector transitions are correct. The text attributes '
                       'them to the full emitter/detector variant and explicitly does not infer '
                       'isolated coding capacity.'},
           {'location': 'Results: unmarked-reference controls',
            'status': 'scope-appropriate',
            'finding': 'Fixed pool controls describe retained calibration behavior; no equal '
                       'population FPR claim is made.'},
           {'location': 'Results: complete marginals',
            'status': 'supported',
            'finding': 'The natural complete labels make J exact for HE, and complete stock/S4 '
                       'MBPP marginals already certify the direction. The evaluation target is '
                       'explicitly earlier label acquisition.'},
           {'location': 'Results: representative J and C certificates',
            'status': 'supported',
            'finding': 'Recomputed every prefix of the four reported schedules independently from '
                       'row coefficients. First counts, exact signed intervals, denominator '
                       'guarantees, and overlapping individual conditional intervals agree.'},
           {'location': 'Results: hash-order sensitivity',
            'status': 'supported',
            'finding': 'All 16 representative shared joint first-certificate counts recomputed '
                       'independently. Ranges are finite fixed-order sensitivity, not confidence '
                       'intervals or optimality guarantees.'},
           {'location': 'Results and S14.3: expanded input',
            'status': 'supported',
            'finding': 'Current V3 counts are 124158 comparable/95 unavailable, with 11 both-side '
                       'encoding timeouts and 8 matching actual exceptions. Task label uses '
                       'outcome equality; poststate/streams are additional checks. Distinct '
                       'fresh-input contract does not establish complete task correctness.'},
           {'location': 'S14.1: study design',
            'status': 'scope-appropriate',
            'finding': 'All complete fixed files and three fixed keys retained; pilots and '
                       'interventions are acknowledged. These are canonical public reference '
                       'programs, not a representative production-system or generated-completion '
                       'sample.'},
           {'location': 'S14.2: contracts and costs',
            'status': 'supported',
            'finding': 'Original assertions determine primary labels; HE trace equality is an '
                       'additional check. Suite cost is one execution; HE function entries and '
                       'MBPP assertion entries remain distinct.'},
           {'location': 'S14.4: observer boundaries',
            'status': 'supported',
            'finding': '24 HE primary,21 expanded,14 MBPP controls retained. Broad catch/timer '
                       'markers and MBPP internally caught resource exceptions are described '
                       'consistently with their different observation contracts.'},
           {'location': 'S14.5: fresh replay',
            'status': 'supported',
            'finding': 'Four independent replays use a registry without candidate labels or '
                       'candidate observation paths; 146+160+1+6=313 queries. Fresh executions are '
                       'separate from read-only receipt verification.'}]}
retained_notes['current_text_matches_reviewed_snapshot'] = {
    name: INPUT_HASHES.get(name) == digest
    for name, digest in retained_notes['reviewed_text_sha256'].items()
}
retained_notes['changed_text_requiring_manual_review'] = [
    name for name, matches in retained_notes['current_text_matches_reviewed_snapshot'].items()
    if not matches
]
review['retained_manual_review_notes'] = retained_notes
review['status_scope'] = 'PASS applies to the automated fixed-study checks only; retained manual notes are reported separately.'
payload = json.dumps(review, ensure_ascii=False, indent=2)+'\n'
if OUT is None:
    sys.stdout.write(payload)
else:
    # Exclusive creation prevents an accidental overwrite of a source ledger.
    with OUT.open('x', encoding='utf-8') as stream:
        stream.write(payload)
    print(json.dumps({'status':'PASS', 'output':str(OUT),
                      'output_sha256':hashlib.sha256(payload.encode('utf-8')).hexdigest(),
                      'script_sha256':review['script_sha256'],
                      'fresh_manual_review_performed':False}))
