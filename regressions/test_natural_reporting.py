"""Independent reporting checks for the current natural-program study.

These checks read delivered sources, unchanged benchmark contracts and native
observations. No producer, normalizer, watermark implementation, or analysis
implementation is imported. Current paired, native-cost and CREST reporting is checked separately.
"""
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATURAL = ROOT / 'results/revision-sew-natural'
KEYS = {'upstream_default': '76767676767676767676767676767676',
        'integer_0': '00000000000000000000000000000000',
        'integer_1': '00000000000000000000000000000001'}
VARIANTS = ('stock', 's1', 's4', 's1_s4')
MBPP_VARIANTS = {'stock': 'stock', 's1_literal_predecessor': 's1',
                 's4_return_boundary': 's4', 's1_s4': 's1_s4'}
EXPECTED = {'HumanEval': {'stock': (492, 492, 368, 368), 's1': (492, 492, 365, 365),
                         's4': (492, 492, 368, 368), 's1_s4': (492, 492, 365, 365)},
            'Sanitized MBPP': {'stock': (1281, 1278, 849, 849), 's1': (1281, 1278, 843, 843),
                               's4': (1281, 1281, 852, 852), 's1_s4': (1281, 1281, 846, 846)}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical_digest(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode('utf-8'))


@lru_cache(maxsize=None)
def file_bytes(path):
    return Path(path).read_bytes()


@lru_cache(maxsize=None)
def json_file(path):
    raw = file_bytes(path)
    if str(path).endswith('.gz'):
        raw = gzip.decompress(raw)
    return json.loads(raw)


def checked_bytes(path, expected):
    value = file_bytes(path)
    require(digest(value) == expected, 'Source or observation digest differs: ' + str(path))
    return value


def checked_json(path, expected, canonical=False):
    value = json_file(path)
    actual = canonical_digest(value) if canonical else digest(file_bytes(path))
    require(actual == expected, 'Contract or observation digest differs: ' + str(path))
    return value


def source_contract(row):
    return canonical_digest({name: row[name] for name in
                             ('reference_sha256', 'candidate_sha256', 'contract_sha256')})


def mbpp_observed_label(observation, expected_entries):
    """Reconstruct finite-suite support from retained native events, not a row label."""
    events = observation['events']
    require(not any(e['status'] == 'evidence_rejected' for e in events),
            'Rejected evidence cannot enter the primary comparison')
    failures = [e for e in events if e['event'] in ('source_compile', 'test_result')
                and e['status'] == 'failed']
    if failures:
        # Genuine witnesses survive a later resource interruption.
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


@lru_cache(maxsize=1)
def observed_rows():
    """Join native observations to exact reference/candidate/contract identities."""
    result = []
    root = NATURAL / 'humaneval'
    data = {task['task_id']: task for task in
            map(json.loads, gzip.decompress(file_bytes(root / 'data/HumanEval.jsonl.gz')).decode().splitlines())}
    require(set(data) == {'HumanEval/' + str(i) for i in range(164)}, 'HumanEval population changed')
    references = {r['task_id']: r for r in json_file(root / 'references.json')}
    require(set(references) == set(data), 'HumanEval reference denominator changed')
    for row in json_file(root / 'rows.json'):
        task = data[row['task_id']]
        reference = references[row['task_id']]
        checked_bytes(root / row['source_path'], row['candidate_sha256'])
        reference_source = checked_bytes(root / reference['source_path'], row['reference_sha256'])
        require(reference_source == (task['prompt'] + task['canonical_solution']).encode(),
                'HumanEval reference differs from the unchanged canonical solution')
        require(reference['contract_sha256'] == row['contract_sha256'], 'Reference contract differs')
        contract = checked_json(root / 'contracts' / (row['contract_sha256'] + '.json'),
                                row['contract_sha256'], canonical=True)
        require(contract['test_body'] == task['test'] and contract['entry_point'] == task['entry_point'],
                'HumanEval original test contract changed')
        require(contract['original_test_utf8_sha256'] == digest(task['test'].encode()),
                'HumanEval original-test digest differs')
        require(contract['reference_source_sha256'] == row['reference_sha256'], 'Reference binding differs')
        require(contract['observer_sha256'] == digest(file_bytes(root / 'native_runner.py')),
                'HumanEval observation identity differs')
        for field in ('platform', 'python_build', 'interpreter_executable_sha256'):
            require(bool(contract[field]), 'HumanEval exact runtime binding missing: ' + field)
        ref_observation = checked_json(root / reference['observations_path'], reference['observations_sha256'])
        observation = checked_json(root / row['observation_path'], row['observation_sha256'])
        require(canonical_digest(observation) == row['semantic_observation_sha256'],
                'HumanEval semantic observation digest differs')
        require(ref_observation['status'] == 'passed' and reference['status'] == 'passed',
                'A failed reference cannot admit candidate preservation evidence')
        # Full call-record equality is deliberately not part of this validity
        # definition: the unchanged check(candidate) suite is the primary oracle.
        valid = 1 if observation['status'] == 'passed' else (0 if observation['status'] == 'failed' else None)
        declared = {'supported': 1, 'contradicted': 0, 'unavailable': None}[row['validity_label']]
        require(valid == declared and row['candidate_status'] == observation['status'],
                'HumanEval row validity differs from native original-suite evidence')
        require(row['candidate_function_invocations'] == len(observation['observations']),
                'HumanEval function-invocation unit changed')
        detected = row['detector']['verdict'] == 'Watermark detected'
        require(row['detected'] == detected, 'HumanEval row detector verdict differs')
        result.append(dict(row, corpus='HumanEval', valid=valid, detected=detected,
                           reference_detected=row['reference_detector']['verdict'] == 'Watermark detected'))

    root = NATURAL / 'mbpp'
    dataset = ROOT / 'external-studies/sew_natural/mbpp/sanitized-mbpp.json'
    data = {task['task_id']: task for task in json_file(dataset)}
    require(len(data) == 427 and sum(len(t['test_list']) for t in data.values()) == 1324,
            'Complete sanitized-MBPP population or original assertions changed')
    raw_rows = {}
    for original in MBPP_VARIANTS:
        for row in json_file(root / 'factors' / original / 'rows.json'):
            coordinate = original, row['task_id'], row['key_id']
            require(coordinate not in raw_rows, 'Duplicate raw MBPP coordinate')
            raw_rows[coordinate] = row
    for row in json_file(root / 'factors/normalized_rows.json'):
        task = data[row['original_task_id']]
        raw = raw_rows[row['variant'], row['original_task_id'], row['key_id']]
        require(row['task_id'] == 'MBPP/' + str(task['task_id']), 'MBPP task mapping differs')
        checked_bytes(root / row['source_path'], row['candidate_sha256'])
        require(checked_bytes(root / row['reference_path'], row['reference_sha256']) == task['code'].encode(),
                'MBPP reference differs from unchanged canonical source')
        contract = checked_json(root / row['contract_path'], row['contract_sha256'], canonical=True)
        native = checked_json(root / row['native_contract_path'], row['native_contract_sha256'], canonical=True)
        require(contract['native_contract'] == native and
                contract['native_contract_sha256'] == row['native_contract_sha256'],
                'MBPP normalized contract does not bind its original native contract')
        require(native['test_list'] == task['test_list'] and native['test_imports'] == task['test_imports'],
                'MBPP original assertions/imports changed')
        require(native['evidence_schema'] == 'markvalidity-mbpp-original-assertions-v2',
                'Historical MBPP observer supplied as current')
        runner = ROOT / 'external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'
        require(native['native_runner_sha256'] == digest(file_bytes(runner)), 'MBPP observer identity differs')
        environment = contract['execution_environment']
        require(native['execution_environment'] == environment, 'MBPP runtime differs between producer and receiver')
        for field in ('platform', 'python_build', 'sys_version', 'interpreter_executable_sha256'):
            require(bool(environment[field]), 'MBPP exact runtime binding missing: ' + field)
        ref_observation = checked_json(root / row['reference_observation_path'], row['reference_observation_sha256'])
        observation = checked_json(root / row['observation_path'], row['observation_sha256'])
        require(mbpp_observed_label(ref_observation, len(task['test_list'])) == 1,
                'MBPP reference does not support the stated contract')
        valid = mbpp_observed_label(observation, len(task['test_list']))
        detected = raw['detector']['verdict'] == 'Watermark detected'
        require(row['evidence_admission'] == 'accepted', 'Rejected or unavailable MBPP evidence admitted')
        require(valid == row['validity_label'] and detected == row['detected'],
                'MBPP normalized outcome differs from raw native/detector evidence')
        require(raw['candidate_sha256'] == row['candidate_sha256'] and
                raw['reference_sha256'] == row['reference_sha256'], 'MBPP detector/source linkage differs')
        require(row['assertion_entries'] == len(task['test_list']) and
                row['observed_assertion_entries'] == len(task['test_list']), 'MBPP assertion-entry unit changed')
        result.append(dict(row, corpus='Sanitized MBPP', variant=MBPP_VARIANTS[row['variant']],
                           valid=valid, detected=detected,
                           reference_detected=raw['reference_detector']['verdict'] == 'Watermark detected'))
    return result


def score(rows):
    n = len(rows)
    require(n > 0, 'Empty population')
    require(all(r['valid'] in (0, 1) for r in rows), 'Exact scores require every validity label')
    v = sum(r['valid'] for r in rows)
    d = sum(r['detected'] for r in rows)
    j = sum(r['valid'] and r['detected'] for r in rows)
    return {'N': n, 'V': v, 'detected': d, 'joint': j,
            'A': Fraction(v, n), 'D': Fraction(d, n), 'J': Fraction(j, n),
            'C': Fraction(j, v) if v else None}


@lru_cache(maxsize=None)
def current_reporting_text(name, artifact=ROOT):
    configuration = json.loads((artifact / 'manuscript-reporting/scopes.json').read_text())['current']
    snapshot = artifact / configuration['passage_root']
    manifest = json.loads((artifact / configuration['snapshot_manifest']).read_text())
    require(manifest['scope'] == 'current-publication', 'Reporting snapshot scope differs')
    for filename, expected in manifest['primary_ledgers_sha256'].items():
        require(digest((artifact / filename).read_bytes()) == expected, 'Current ledger binding is stale: ' + filename)
    for filename, expected in manifest['files_sha256'].items():
        require(digest((snapshot / filename).read_bytes()) == expected, 'Current reporting snapshot changed: ' + filename)
        source = artifact / configuration['integrated_paper'] / filename
        if (artifact / configuration['integrated_paper']).is_dir():
            require(digest(source.read_bytes()) == expected, 'Current manuscript and shipped reporting differ: ' + filename)
    require(name in manifest['files_sha256'], 'Requested current passage is unbound')
    return (snapshot / name).read_text()


def expanded_current_main(artifact=ROOT):
    """Follow bound reporting inputs from main, using LaTeX's paper-root paths."""
    configuration = json.loads((artifact / 'manuscript-reporting/scopes.json').read_text())['current']
    manifest = json.loads((artifact / configuration['snapshot_manifest']).read_text())
    available = manifest['files_sha256']

    def expand(name, ancestors):
        require(name not in ancestors, 'Cyclic current reporting input')
        text = current_reporting_text(name, artifact)

        def include(match):
            child = match.group(1)
            if not child.endswith('.tex'):
                child += '.tex'
            return expand(child, ancestors | {name}) if child in available else match.group(0)

        return re.sub(r'\\input\{([^}]+)\}', include, text)

    return expand('main.tex', set())


class NaturalReportingContractTests(unittest.TestCase):
    def test_complete_populations_and_same_three_keys_for_all_four_versions(self):
        rows = observed_rows()
        self.assertEqual(len(rows), 7092)
        for corpus, n in (('HumanEval', 164), ('Sanitized MBPP', 427)):
            subset = [r for r in rows if r['corpus'] == corpus]
            tasks = {r['task_id'] for r in subset}
            self.assertEqual(len(tasks), n)
            coordinates = [(r['task_id'], r['variant'], r['key_id']) for r in subset]
            self.assertEqual(len(coordinates), len(set(coordinates)))
            self.assertEqual(set(coordinates), set(itertools.product(tasks, VARIANTS, KEYS)))
            for row in subset:
                self.assertEqual(row['key_hex'], KEYS[row['key_id']])
                self.assertEqual(row['suite_cost'], 1)
                self.assertEqual(row['candidate_suite_executions'], 1)
                self.assertEqual(bool(row['joint']), bool(row['valid'] and row['detected']))

    def test_A_D_J_C_counts_denominators_and_primary_D_equals_J(self):
        rows = observed_rows()
        he = {r['variant']: r for r in json_file(NATURAL / 'humaneval/summary.json')['variants']}
        mb = json_file(NATURAL / 'mbpp/factors/comparison_summary.json')
        reverse = {v: k for k, v in MBPP_VARIANTS.items()}
        for corpus, version in itertools.product(EXPECTED, VARIANTS):
            with self.subTest(corpus=corpus, version=version):
                actual = score([r for r in rows if r['corpus'] == corpus and r['variant'] == version])
                self.assertEqual(tuple(actual[k] for k in ('N', 'V', 'detected', 'joint')), EXPECTED[corpus][version])
                self.assertEqual(actual['D'], actual['J'])
                self.assertEqual(actual['C'] * actual['A'], actual['J'])
                if corpus == 'HumanEval':
                    saved = he[version]
                    self.assertEqual((saved['configurations'], saved['validity_labels'], saved['detected'], saved['joint']),
                                     (actual['N'], {'supported': actual['V']}, actual['detected'], actual['joint']))
                    self.assertEqual(saved['candidate_function_invocations'], 4602)
                else:
                    for population in ('per_variant_all_attempts', 'per_variant_reference_passing_subset'):
                        saved = mb[population][reverse[version]]
                        self.assertEqual((saved['attempts'], saved['valid'], saved['detected'], saved['joint']),
                                         EXPECTED[corpus][version])
                        for metric in ('A', 'D', 'J', 'C'):
                            self.assertAlmostEqual(saved[metric], float(actual[metric]), places=14)
                        self.assertEqual(saved['unknown_validity'], 0)
                        self.assertEqual(saved['scheduled_original_assertion_entries'], 3972)
        stock = score([r for r in rows if r['corpus'] == 'Sanitized MBPP' and r['variant'] == 'stock'])
        self.assertNotEqual(stock['A'], stock['D'])  # Reject the historical A/D reporting-field swap.
        self.assertNotEqual(stock['C'], stock['J'])  # Their denominators differ after three failures.

    def test_exact_source_contract_groups_and_free_reference_identities(self):
        rows = observed_rows()
        for corpus, expected_groups, expected_free, expected_free_rows in (
                ('HumanEval', 546, 3, 12), ('Sanitized MBPP', 1347, 22, 80)):
            groups = defaultdict(list)
            for row in (r for r in rows if r['corpus'] == corpus):
                actual = source_contract(row)
                self.assertEqual(row['source_contract_sha256'], actual)
                groups[actual].append(row)
            self.assertEqual(len(groups), expected_groups)
            for members in groups.values():
                self.assertEqual(len({r['valid'] for r in members}), 1)
                self.assertEqual(len({(r['reference_sha256'], r['candidate_sha256'], r['contract_sha256'])
                                      for r in members}), 1)
            free = [r for members in groups.values() for r in members
                    if r['reference_sha256'] == r['candidate_sha256']]
            self.assertEqual(len(free), expected_free_rows)
            self.assertEqual(len({r['source_contract_sha256'] for r in free}), expected_free)
            self.assertTrue(all(r['valid'] == 1 and r['reference_status'] == 'passed' for r in free))
            self.assertEqual(Counter(r['variant'] for r in free),
                             {v: expected_free_rows // 4 for v in VARIANTS})
        # Some identical candidate bytes have different task obligations. They
        # must stay distinct even though these observed labels happen to agree.
        by_candidate = defaultdict(list)
        for row in rows:
            by_candidate[row['candidate_sha256']].append(row)
        collisions = [members for members in by_candidate.values()
                      if len({r['contract_sha256'] for r in members}) > 1]
        self.assertTrue(collisions)
        for members in collisions:
            self.assertGreater(len({source_contract(r) for r in members}), 1)

    def test_S4_repairs_exactly_the_three_observed_MBPP_failures(self):
        rows = {(r['corpus'], r['variant'], r['task_id'], r['key_id']): r for r in observed_rows()}
        expected = {('MBPP/290', 'upstream_default'), ('MBPP/290', 'integer_1'), ('MBPP/393', 'integer_0')}
        for left, right in (('stock', 's4'), ('s1', 's1_s4')):
            changed, failures = set(), set()
            for (corpus, variant, task, key), row in rows.items():
                if corpus != 'Sanitized MBPP' or variant != left:
                    continue
                repaired = rows[corpus, right, task, key]
                if row['candidate_sha256'] != repaired['candidate_sha256']:
                    changed.add((task, key))
                if row['valid'] == 0:
                    failures.add((task, key))
                    self.assertFalse(row['detected'])
                    self.assertEqual((repaired['valid'], repaired['detected']), (1, True))
                    obs = json_file(NATURAL / 'mbpp' / row['observation_path'])
                    tests = [e for e in obs['events'] if e['event'] == 'test_result']
                    self.assertEqual(len(tests), 3)
                    self.assertTrue(all(e['status'] == 'failed' and e['error']['type'] == 'builtins.NameError'
                                        and 'returnmax_length' in e['error']['message'] for e in tests))
            self.assertEqual(changed, expected)
            self.assertEqual(failures, expected)
        for (corpus, variant, task, key), row in rows.items():
            if corpus == 'HumanEval' and variant in ('stock', 's1'):
                other = 's4' if variant == 'stock' else 's1_s4'
                self.assertEqual(row['candidate_sha256'], rows[corpus, other, task, key]['candidate_sha256'])

    def test_unwatermarked_reference_controls_keep_their_original_denominator(self):
        rows = observed_rows()
        for corpus in EXPECTED:
            counts = Counter(r['variant'] for r in rows if r['corpus'] == corpus and r['reference_detected'])
            expected = {} if corpus == 'HumanEval' else {'stock': 3, 's4': 3}
            self.assertEqual(dict(counts), expected)
        self.assertEqual(sum(r['corpus'] == 'HumanEval' for r in rows), 164 * 3 * 4)
        self.assertEqual(sum(r['corpus'] == 'Sanitized MBPP' for r in rows), 427 * 3 * 4)

    def test_current_outcome_table_uses_reconstructed_counts_and_correct_C(self):
        table = current_reporting_text('figdata/natural-outcomes.tex')
        self.assertIn(table, expanded_current_main(), 'The verified outcome table is not included by the current main')
        corpus = None
        found = {}
        versions = {'Stock': 'stock', 'S1': 's1', 'S4': 's4', 'S1+S4': 's1_s4'}
        for line in table.splitlines():
            cells = [re.sub(r'\\\\\s*$', '', c).strip() for c in line.split('&')]
            if len(cells) != 7 or cells[1] not in versions:
                continue
            corpus = cells[0] or corpus
            version = versions[cells[1]]
            self.assertNotIn((corpus, version), found)
            integers = tuple(int(c.replace('\\,', '').replace(',', '')) for c in cells[2:5])
            actual = score([r for r in observed_rows() if r['corpus'] == corpus and r['variant'] == version])
            self.assertEqual(integers, (actual['N'], actual['V'], actual['joint']))
            for cell, metric in zip(cells[5:], ('J', 'C')):
                value = actual[metric]
                rounded = (Decimal(value.numerator) * 100 / Decimal(value.denominator)).quantize(Decimal('.01'))
                self.assertEqual(Decimal(cell), rounded)
            found[corpus, version] = integers
        self.assertEqual(set(found), set(itertools.product(EXPECTED, VARIANTS)))





if __name__ == '__main__':
    unittest.main()
