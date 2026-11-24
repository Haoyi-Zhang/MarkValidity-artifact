"""Independent finite enumeration and receiver controls for natural_analysis.

These controls enumerate mathematical ledgers and use synthetic file envelopes.
They are not additional empirical code-corpus observations.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
from itertools import combinations, product
import json
import csv
import gzip
from pathlib import Path
import random
import tempfile

from natural_analysis import (AuditPolicy, CERTIFICATES, PairState, PublicRow,
    ScoreState, SealedOracle, canonical_bytes, digest, load_ledgers, run_schedule, source_contract_id)

HERE = Path(__file__).resolve().parent


def direct_outcomes(left, right, admitted):
    keys = sorted((set(left) | set(right)) - set(admitted))
    outcomes = []
    for bits in product((False, True), repeat=len(keys)):
        labels = dict(admitted, **dict(zip(keys, bits)))
        scores = []
        for model in (left, right):
            n = sum(a for g, (a, b) in model.items() if labels[g])
            a = sum(b for g, (j, b) in model.items() if labels[g])
            scores.append((n, a, Fraction(n, a) if a else None))
        outcomes.append(scores)
    return outcomes


def decision_for(values):
    return ('left_strict' if min(values) > 0 else 'right_strict' if max(values) < 0
            else 'tie' if set(values) == {0} else 'unresolved')


def check_state(state, left, right):
    actual = direct_outcomes(left, right, state.admitted)
    snapshot = state.snapshot()
    for coordinate, metric in enumerate(('J', 'A')):
        gaps = [pair[0][coordinate] - pair[1][coordinate] for pair in actual]
        bound = snapshot[f'coupled_{metric}']
        assert (bound['lower'], bound['upper']) == (min(gaps), max(gaps))
        assert bound['decision'] == decision_for(gaps)
        separated = snapshot[f'independent_{metric}']
        assert separated['lower'] <= min(gaps) <= max(gaps) <= separated['upper']
    for side, name in enumerate(('left', 'right')):
        defined = [pair[side][2] for pair in actual if pair[side][2] is not None]
        bound = snapshot[f'{name}_C']
        assert bound['defined_some'] == bool(defined)
        assert bound['defined_all'] == (len(defined) == len(actual))
        if defined:
            assert (bound['lower'], bound['upper']) == (min(defined), max(defined))
        else:
            assert bound['lower'] is bound['upper'] is None
    both = [pair for pair in actual if pair[0][2] is not None and pair[1][2] is not None]
    coupled = snapshot['coupled_C']
    if not state.different:
        assert coupled['route'] == 'exact_common_remainder'
        if both:
            margins = [pair[0][0] * pair[1][1] - pair[1][0] * pair[0][1] for pair in both]
            assert (coupled['lower'], coupled['upper']) == (min(margins), max(margins))
            differences = [pair[0][2] - pair[1][2] for pair in both]
            assert coupled['relation_on_defined'] == decision_for(differences)
        else:
            assert coupled['lower'] is coupled['upper'] is None
    for method in ('coupled', 'independent'):
        bound = snapshot[f'{method}_C']
        if bound['decision'] in CERTIFICATES:
            assert len(both) == len(actual)
            assert bound['decision'] == decision_for([p[0][2] - p[1][2] for p in both])
    return len(actual), len(actual) - len(both)


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('invalid input was accepted')


def receiving_controls():
    controls = []
    with tempfile.TemporaryDirectory(prefix='markvalidity-receiver-') as name:
        root = Path(name)
        (root / 'sources').mkdir()
        (root / 'contracts').mkdir()
        (root / 'observations').mkdir()
        source = b'def f():\n    return 1\n'
        reference = b'def f():\n    return 1  # reference\n'
        source_hash, reference_hash = digest(source), digest(reference)
        (root / 'sources' / f'{source_hash}.py').write_bytes(source)
        (root / 'sources' / f'{reference_hash}.py').write_bytes(reference)
        contracts = []
        for seed in (0, 1):
            contract = dict(reference_source_sha256=reference_hash, seed=seed,
                            initialization='synthetic finite contract', runtime='synthetic')
            h = digest(canonical_bytes(contract))
            (root / 'contracts' / f'{h}.json').write_bytes(canonical_bytes(contract) + b'\n')
            contracts.append(h)
        observations = {}
        for state in ('passed', 'failed', 'timeout'):
            data = canonical_bytes({'status': state})
            h = digest(data)
            p = f'observations/{h}.json'
            (root / p).write_bytes(data)
            observations[state] = (p, h)
        rows = []
        for index, variant in enumerate(('stock', 's1', 's4', 's1_s4')):
            contract_hash = contracts[index // 2]
            validity = index // 2 == 0
            observation_path, observation_hash = observations['passed' if validity else 'failed']
            rows.append(dict(dataset='synthetic', task_id='task0', key_id='key0', key_hex='00',
                variant=variant, detected=index % 2 == 0, suite_cost=1,
                reference_sha256=reference_hash, candidate_sha256=source_hash,
                contract_sha256=contract_hash,
                source_contract_sha256=source_contract_id(reference_hash, source_hash, contract_hash),
                source_path=f'sources/{source_hash}.py', reference_path=f'sources/{reference_hash}.py',
                contract_path=f'contracts/{contract_hash}.json', observation_path=observation_path,
                observation_sha256=observation_hash,
                reference_observation_path=observations['passed'][0],
                reference_observation_sha256=observations['passed'][1],
                candidate_status='passed' if validity else 'failed', reference_status='passed',
                validity_label=validity, joint=validity and index % 2 == 0))
        ledger_path = root / 'rows.json'
        def load(records):
            ledger_path.write_text(json.dumps(records))
            return load_ledgers([(ledger_path, root)])
        ledger, labels = load(rows)
        assert len(ledger.groups) == 2 and sorted(labels.values()) == [False, True]
        controls.append('same source under different contracts is not reused')
        assert source_contract_id(reference_hash, source_hash, contracts[0]) != source_contract_id(source_hash, source_hash, contracts[0])
        controls.append('reference identity changes group identity')
        public_fields = set(asdict(ledger.rows[0]))
        assert not public_fields & {'validity_label', 'joint', 'candidate_status', 'candidate_elapsed_seconds', 'candidate_function_invocations', 'assertion_entries'}
        controls.append('public policy rows omit sealed labels and measured costs')
        assert ledger.rows[0].group == ledger.rows[1].group and ledger.rows[0].detected != ledger.rows[1].detected
        controls.append('same validity group may have different detector outcomes')
        bad = deepcopy(rows)
        bad[0]['source_contract_sha256'] = source_hash
        reject(lambda: load(bad)); controls.append('source-only identity rejected')
        bad = deepcopy(rows)
        bad[0]['suite_cost'] = True
        reject(lambda: load(bad)); controls.append('noninteger declared suite cost rejected')
        bad = deepcopy(rows)
        bad[0]['joint'] = False
        reject(lambda: load(bad)); controls.append('stored joint inconsistency rejected')
        bad = deepcopy(rows)
        bad[1]['validity_label'] = False
        bad[1]['joint'] = False
        bad[1]['candidate_status'] = 'failed'
        bad[1]['observation_path'], bad[1]['observation_sha256'] = observations['failed']
        reject(lambda: load(bad)); controls.append('contradictory labels within one group rejected')
        bad = deepcopy(rows)
        bad[0]['key_id'] = 'unpaired-key'
        reject(lambda: load(bad)); controls.append('mismatched attempted workloads rejected')
        bad = deepcopy(rows)
        bad[0]['source_path'] = '../outside.py'
        reject(lambda: load(bad)); controls.append('asset path escape rejected')
        source_path = root / 'sources' / f'{source_hash}.py'
        source_path.write_bytes(source + b'# tampered\n')
        reject(lambda: load(rows)); controls.append('source byte corruption rejected')
        source_path.write_bytes(source)
        unavailable = deepcopy(rows)
        for record in unavailable[:2]:
            record['validity_label'] = None
            record['candidate_status'] = 'timeout'
            record['observation_path'], record['observation_sha256'] = observations['timeout']
        _, result = load(unavailable)
        assert result[rows[0]['source_contract_sha256']] is None
        controls.append('unavailable execution retained as unknown')
    return controls


def main():
    if not __debug__:
        raise SystemExit('run without -O; the independent oracle uses assertions')
    rng = random.Random(725148)
    systems = states = completions = undefined = 0
    # Include arbitrary within-source detector mixtures; a group is not assumed
    # to have one fixed D across keys or versions.
    for length in range(1, 7):
        for _ in range(60):
            left, right = {}, {}
            for g in range(length):
                bl, br = rng.randrange(4), rng.randrange(4)
                if bl: left[f'g{g}'] = (rng.randrange(bl + 1), bl)
                if br: right[f'g{g}'] = (rng.randrange(br + 1), br)
            ml, mr = sum(b for a, b in left.values()), sum(b for a, b in right.values())
            if ml == mr == 0:
                left['nonempty'] = right['nonempty'] = (0, 1)
                ml = mr = 1
            if ml < mr:
                left['fill-left'] = (rng.randrange(mr - ml + 1), mr - ml)
            if mr < ml:
                right['fill-right'] = (rng.randrange(ml - mr + 1), ml - mr)
            denominator = max(ml, mr)
            state = PairState(left, right, denominator)
            order = sorted(state.groups)
            rng.shuffle(order)
            labels = {g: bool(rng.randrange(2)) for g in order}
            for group in [None] + order:
                if group is not None:
                    state.reveal(group, labels[group])
                c, u = check_state(state, left, right)
                completions += c; undefined += u; states += 1
            systems += 1
    # Equal-coefficient remainder controls, including zero denominators.
    choices = ((0, 1), (1, 1), (0, 2), (1, 2), (2, 2))
    for length in range(4):
        for common in product(choices, repeat=length):
            for nl, al, nr, ar in ((0, 0, 0, 0), (0, 0, 1, 1), (1, 2, 2, 3),
                                  (2, 3, 1, 2), (0, 2, 0, 3)):
                left = {f'c{i}': value for i, value in enumerate(common)}
                right = dict(left)
                if al: left['known-left'] = (nl, al)
                if ar: right['known-right'] = (nr, ar)
                mass = max(al, ar)
                if mass > al: left['invalid-left'] = (0, mass - al)
                if mass > ar: right['invalid-right'] = (0, mass - ar)
                denominator = mass + sum(b for a, b in common)
                if denominator == 0:
                    continue
                state = PairState(left, right, denominator)
                for g in ('known-left', 'known-right', 'invalid-left', 'invalid-right'):
                    if g in state.groups:
                        state.reveal(g, g.startswith('known'))
                c, u = check_state(state, left, right)
                completions += c; undefined += u; states += 1; systems += 1
    controls = receiving_controls()
    reject(lambda: ScoreState({'bad': (1, 0)})); controls.append('positive detection with zero row mass rejected')
    reject(lambda: PairState({'x': (1, 1)}, {'y': (1, 2)}, 1)); controls.append('unequal workload denominators rejected')
    left = {'g': (1, 2)}
    right = {'g': (2, 2)}
    state = PairState(left, right, 2)
    assert state.snapshot()['coupled_J']['lower'] == -1
    assert state.snapshot()['independent_J']['lower'] == -2
    reject(lambda: state.common_conditional())
    controls.append('different coefficient pairs block common-remainder certificate')
    state.reveal('g', False)
    assert state.snapshot()['coupled_C']['decision'] == 'undefined_everywhere_for_at_least_one_side'
    controls.append('0/0 is undefined, never conditional score zero')
    same = {'g0': (1, 2), 'g1': (0, 1)}
    state = PairState(same, same, 3)
    assert state.snapshot()['coupled_J']['decision'] == 'tie'
    assert state.snapshot()['coupled_A']['decision'] == 'tie'
    assert state.snapshot()['coupled_C']['decision'] == 'undefined_possible'
    state.reveal('g0', True)
    assert state.snapshot()['coupled_C']['decision'] == 'tie'
    controls.append('identical methods certify equality, never a strict winner')
    state = PairState(left, right, 2)
    state.reveal('g', None)
    assert not state.admitted and state.different == {'g'}
    controls.append('unavailable query does not resolve a coefficient-different group')
    reject(lambda: state.reveal('g', True)); controls.append('requery rejected by the one-suite disclosure experiment')

    # Query selection cannot depend on labels that were not disclosed. Exhaust
    # every completion of this mixed shared/private synthetic ledger.
    left = {'a': (2, 2), 'b': (1, 2), 'c': (0, 2), 'left': (1, 1)}
    right = {'a': (2, 2), 'b': (1, 2), 'c': (0, 2), 'right': (0, 1)}
    keys = sorted(set(left) | set(right))
    policy_names = ['configuration_first', 'joint_width_per_suite', 'behavior_width_per_suite',
                    'conditional_differences_first'] + [f'hash_{i:02d}' for i in range(16)]
    schedule_tests = width_tests = 0
    for policy_name in policy_names:
        histories = {}
        fixed_orders = set()
        for bits in product((False, True), repeat=len(keys)):
            labels = dict(zip(keys, bits))
            state = PairState(left, right, 7)
            policy = AuditPolicy(policy_name, state, keys)
            oracle = SealedOracle(labels)
            order = []
            while True:
                # Equal public state / revealed transcript must produce the same
                # next choice across every hidden completion.
                history = tuple((g, labels[g]) for g in order)
                selected = policy.next_group(state)
                assert history not in histories or histories[history] == selected
                histories[history] = selected
                if selected is None: break
                old_j_width = state.joint.upper - state.joint.lower
                old_a_width = state.behavior.upper - state.behavior.lower
                label = oracle.query(selected)
                state.reveal(selected, label)
                assert old_j_width - (state.joint.upper - state.joint.lower) == abs(state.joint.coefficients[selected])
                assert old_a_width - (state.behavior.upper - state.behavior.lower) == abs(state.behavior.coefficients[selected])
                order.append(selected)
                if policy_name in ('joint_width_per_suite', 'behavior_width_per_suite'):
                    coordinate = state.joint if policy_name.startswith('joint') else state.behavior
                    observed = coordinate.upper - coordinate.lower
                    best = min(sum(abs(coordinate.coefficients[g]) for g in keys if g not in subset)
                               for subset in combinations(keys, len(order)))
                    assert observed == best
                    width_tests += 1
            fixed_orders.add(tuple(order))
            schedule_tests += 1
        if policy_name != 'conditional_differences_first':
            assert len(fixed_orders) == 1
    controls.append('all 16 hash orders and coefficient policies are blind to undisclosed labels')
    for name in policy_names:
        identical = {'reference': (0, 1), 'remaining': (1, 1)}
        oracle = SealedOracle({'reference': True, 'remaining': False})
        result = run_schedule((identical, identical, 2, ['reference', 'remaining']), name, oracle,
                              {'reference': 0, 'remaining': 1}, initial_labels={'reference': True})
        assert oracle.requests == ['remaining']
        assert result['suite_queries'] == 1 and result['initially_admitted_groups'] == 1
        for metric in ('J', 'A', 'C'):
            assert result['first_certificates'][f'coupled_{metric}']['suite_queries'] == 0
            assert result['first_certificates'][f'coupled_{metric}']['decision'] == 'tie'
    controls.append('reference identity admission costs zero and is excluded from every query schedule')
    with tempfile.TemporaryDirectory(prefix='markvalidity-trace-') as directory:
        trace = Path(directory) / 'trace.csv.gz'
        l = {'common': (1, 2), 'left': (1, 1)}
        r = {'common': (1, 2), 'right': (0, 1)}
        run_schedule((l, r, 3, ['common', 'left', 'right']), 'conditional_differences_first',
                     SealedOracle({'common': True, 'left': True, 'right': False}),
                     {'common': 0, 'left': 1, 'right': 2}, trace)
        with gzip.open(trace, 'rt') as stream:
            records = list(csv.DictReader(stream))
        assert len(records) == 4
        for record in records:
            assert None not in record
            if record['coupled_C_route'] == 'exact_common_remainder':
                assert record['coupled_C_separate_gap_lower'] == record['coupled_C_separate_gap_upper'] == ''
            else:
                assert record['coupled_C_margin_lower'] == record['coupled_C_margin_upper'] == ''
    controls.append('CSV conditional margins and rate gaps occupy separate fixed-unit columns')
    controls.append('unit-cost linear-width policy attains exhaustive fixed-budget width optimum')
    report = dict(status='PASS', coefficient_systems=systems, state_prefixes=states,
                  direct_Boolean_completions=completions, undefined_completions=undefined,
                  full_schedule_assignments=schedule_tests, fixed_budget_width_checks=width_tests,
                  receiving_and_boundary_controls=controls,
                  scope='Synthetic finite-ledger oracle and file-envelope checks, not empirical program trials.',
                  files_sha256={name: sha256((HERE / name).read_bytes()).hexdigest()
                                for name in ('natural_analysis.py', 'verify_natural_analysis.py')})
    (HERE / 'natural_verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
