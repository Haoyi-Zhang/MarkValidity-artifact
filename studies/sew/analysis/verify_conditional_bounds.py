"""Exhaustive completion oracle for the isolated conditional-bound prototype."""
from __future__ import annotations
from dataclasses import asdict
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random

from conditional_bounds import (UnknownGroup as G, ScoreModel as M, conditional_bounds,
    common_remainder_comparison, conditional_comparison, different_unknown_groups,
    reveal, joint_comparison)

HERE = Path(__file__).resolve().parent


def oracle(models):
    """Independent direct Boolean enumeration; no production bound/evaluate calls."""
    keys = sorted({g.identity for m in models for g in m.unknown})
    outcomes = []
    for values in product((False, True), repeat=len(keys)):
        labels = dict(zip(keys, values))
        rows = []
        for m in models:
            n = m.known_joint + sum((g.detected_mass for g in m.unknown if labels[g.identity]), F())
            a = m.known_valid + sum((g.mass for g in m.unknown if labels[g.identity]), F())
            rows.append((n, a, n / a if a else None))
        outcomes.append((labels, rows))
    return outcomes


def serial(value):
    if isinstance(value, F): return str(value)
    if isinstance(value, dict): return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [serial(v) for v in value]
    return value


def single_check(model):
    outcomes = oracle((model,))
    rates = [rows[0][2] for _, rows in outcomes if rows[0][2] is not None]
    result = conditional_bounds(model)
    assert result['defined_for_some_completion'] == bool(rates)
    assert result['defined_for_all_completions'] == (len(rates) == len(outcomes))
    if rates:
        assert result['lower'] == min(rates) and result['upper'] == max(rates)
        for which in ('lower', 'upper'):
            row = next(rows[0] for labels, rows in outcomes if labels == result[which + '_completion'])
            assert row[2] == result[which]
    else:
        assert result['lower'] is result['upper'] is None
    return len(outcomes), len(outcomes) - len(rates)


def pair_check(left, right):
    outcomes = oracle((left, right))
    result = common_remainder_comparison(left, right)
    defined = [(labels, rows) for labels, rows in outcomes
               if rows[0][2] is not None and rows[1][2] is not None]
    assert result['defined_for_some_completion'] == bool(defined)
    assert result['defined_for_all_completions'] == (len(defined) == len(outcomes))
    if defined:
        margins = [rows[0][0] * rows[1][1] - rows[1][0] * rows[0][1] for _, rows in defined]
        assert result['margin_lower'] == min(margins) and result['margin_upper'] == max(margins)
        for which in ('lower', 'upper'):
            rows = next(rows for labels, rows in defined if labels == result[which + '_completion'])
            assert rows[0][0] * rows[1][1] - rows[1][0] * rows[0][1] == result['margin_' + which]
        differences = [rows[0][2] - rows[1][2] for _, rows in defined]
        expected = ('left_strict' if min(differences) > 0 else 'right_strict' if max(differences) < 0
                    else 'tie' if set(differences) == {F()} else 'unresolved')
        assert result['relation_on_defined_completions'] == expected
        assert result['can_stop_for_strict_ordering'] == (len(defined) == len(outcomes) and expected in ('left_strict', 'right_strict'))
        if len(defined) < len(outcomes): assert result['decision'] == 'undefined_possible'
    else:
        assert result['margin_lower'] is result['margin_upper'] is None
        assert result['decision'] == 'undefined_everywhere'
    joint = joint_comparison(left, right)
    gaps = [rows[0][0] - rows[1][0] for _, rows in outcomes]
    assert (joint['lower'], joint['upper']) == (min(gaps), max(gaps))
    return len(outcomes), len(outcomes) - len(defined)


def main():
    if not __debug__:
        raise SystemExit('Run without -O: this independent oracle uses assertions.')
    bases = [(F(n), F(a)) for a in range(3) for n in range(a + 1)]
    choices = [(F(a), F(n)) for a in (1, 2) for n in range(a + 1)]
    single_systems = pair_systems = completions = undefined_completions = 0
    for length in range(4):
        for weights in product(choices, repeat=length):
            groups = tuple(G(f'g{i}', a, n) for i, (a, n) in enumerate(weights))
            for numerator, mass in bases:
                c, u = single_check(M(numerator, mass, groups))
                single_systems += 1; completions += c; undefined_completions += u
            for (nl, al), (nr, ar) in product(bases, repeat=2):
                c, u = pair_check(M(nl, al, groups), M(nr, ar, groups))
                pair_systems += 1; completions += c; undefined_completions += u

    rng = random.Random(918341)
    generic_systems = 300
    for _ in range(generic_systems):
        length = rng.randrange(1, 7)
        models = []
        for side in range(2):
            known = rng.randrange(5)
            groups = []
            for i in range(length):
                mass = rng.randrange(5)
                groups.append(G(f'g{i}', F(mass, 17), F(rng.randrange(mass + 1), 17)))
            models.append(M(F(rng.randrange(known + 1), 17), F(known, 17), tuple(groups)))
        left, right = models
        for model in models:
            c, u = single_check(model); single_systems += 1; completions += c; undefined_completions += u
        before = conditional_comparison(left, right)
        outcomes = oracle((left, right))
        if before['decision'] in ('left_strict', 'right_strict', 'tie'):
            values = [rows[0][2] - rows[1][2] for _, rows in outcomes]
            assert all(value > 0 for value in values) if before['decision'] == 'left_strict' else (
                all(value < 0 for value in values) if before['decision'] == 'right_strict' else set(values) == {F()})
        # A deterministic, label-blind group plan resolves all and only the
        # coefficient differences. Applying one actual completion is receiving,
        # not information used to choose that plan.
        plan = different_unknown_groups(left, right)
        labels = {f'g{i}': bool(rng.randrange(2)) for i in range(length)}
        for key in plan:
            left, right = reveal(left, key, labels[key]), reveal(right, key, labels[key])
        assert different_unknown_groups(left, right) == ()
        c, u = pair_check(left, right); pair_systems += 1; completions += c; undefined_completions += u

    def reject(call):
        try: call()
        except ValueError: return
        raise AssertionError('invalid evidence model was accepted')
    controls = []
    reject(lambda: G('x', 0.1, F(0))); controls.append('float weights rejected')
    reject(lambda: G('x', F(-1), F(0))); controls.append('negative mass rejected')
    reject(lambda: G('x', F(1), F(2))); controls.append('detected mass above total rejected')
    reject(lambda: M(F(2), F(1), ())); controls.append('inconsistent known masses rejected')
    reject(lambda: M(F(0), F(0), (G('x', F(1), F(1)), G('x', F(1), F(0))))); controls.append('duplicate unresolved identities rejected')
    reject(lambda: reveal(M(F(0), F(0), ()), 'x', 1)); controls.append('non-Boolean admitted labels rejected')
    reject(lambda: common_remainder_comparison(M(F(1), F(1), (G('x', F(1), F(1)),)), M(F(1), F(1), (G('x', F(2), F(1)),)))); controls.append('unequal common coefficients rejected')

    absent = M(F(0), F(0), ())
    assert conditional_bounds(absent)['defined_for_some_completion'] is False
    assert common_remainder_comparison(absent, absent)['decision'] == 'undefined_everywhere'
    controls.append('all-invalid completion has no conditional score')
    unknown_equal = M(F(0), F(0), (G('same', F(1), F(1)),))
    equal = common_remainder_comparison(unknown_equal, unknown_equal)
    assert equal['decision'] == 'undefined_possible' and equal['relation_on_defined_completions'] == 'tie'
    resolved_equal = common_remainder_comparison(reveal(unknown_equal, 'same', True), reveal(unknown_equal, 'same', True))
    assert resolved_equal['decision'] == 'tie' and not resolved_equal['can_stop_for_strict_ordering']
    controls.append('identical versions never produce a strict winner')

    shared = (G('shared-undetected', F(5), F(0)),)
    left, right = M(F(4), F(5), shared), M(F(3), F(5), shared)
    pair = common_remainder_comparison(left, right)
    lb, rb = conditional_bounds(left), conditional_bounds(right)
    assert lb['lower'] - rb['upper'] < 0 and pair['decision'] == 'left_strict'
    examples = {'coupled_conditional_certificate_despite_overlap': {
        'left': asdict(left), 'right': asdict(right), 'left_C_bounds': lb, 'right_C_bounds': rb,
        'separate_interval_difference': [lb['lower'] - rb['upper'], lb['upper'] - rb['lower']],
        'coupled_margin': pair, 'actual_C_gap_values': sorted({rows[0][2] - rows[1][2] for _, rows in oracle((left, right))})}}
    shared = (G('shared-detected', F(2), F(2)),)
    left, right = M(F(2), F(8), shared), M(F(1), F(5), shared)
    assert joint_comparison(left, right)['relation'] == 'left_strict'
    assert common_remainder_comparison(left, right)['decision'] == 'unresolved'
    examples['same_joint_winner_but_conditional_order_reverses'] = {
        'left': asdict(left), 'right': asdict(right), 'joint': joint_comparison(left, right),
        'conditional': common_remainder_comparison(left, right),
        'completions': [{'labels': labels, 'left_C': rows[0][2], 'right_C': rows[1][2]}
                        for labels, rows in oracle((left, right))]}
    shared = (G('shared-detected', F(2), F(2)),)
    left, right = M(F(0), F(0), shared), M(F(1), F(3), shared)
    pair = common_remainder_comparison(left, right)
    assert pair['margin_lower'] == F(4) and pair['decision'] == 'undefined_possible'
    assert pair['relation_on_defined_completions'] == 'left_strict' and not pair['can_stop_for_strict_ordering']
    controls.append('strict order on defined completions does not erase possible undefinedness')
    examples['conditional_order_when_defined_is_not_an_unconditional_certificate'] = pair
    (HERE / 'examples.json').write_text(json.dumps(serial(examples), indent=2) + '\n')
    report = dict(status='PASS', single_score_systems=single_systems,
                  common_remainder_pair_systems=pair_systems,
                  generic_coefficient_difference_audit_systems=generic_systems,
                  Boolean_completions_checked=completions,
                  undefined_completion_cases_retained=undefined_completions,
                  invalid_input_and_boundary_controls=controls,
                  scope='Independent complete Boolean enumeration for exact score bounds, endpoint witnesses, comparison margins, joint gaps and stopping decisions. These are mathematical controls, not empirical program trials.',
                  files_sha256={name: sha256((HERE / name).read_bytes()).hexdigest()
                                for name in ['conditional_bounds.py', 'verify_conditional_bounds.py', 'examples.json']})
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
