#!/usr/bin/env python3
"""Exhaustively check emission-aware marginals and operational state identities."""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from operational_state import OperationalPairState
from paired_conditional import PairedEnvelope


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    spec = importlib.util.spec_from_file_location('emission_api', args.artifact / 'external-studies/sew_natural/analysis/natural_analysis.py')
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    states = [(0, None, None)] + [(1, v, d) for v, d in itertools.product((0, 1), repeat=2)]
    models = 0
    marginal_cells = 0
    for n in range(1, 6):
        outcomes = defaultdict(set)
        for rows in itertools.product(states, repeat=n):
            emitted = sum(e for e, v, d in rows)
            valid = sum(v for e, v, d in rows if e)
            detected = sum(d for e, v, d in rows if e)
            joint = sum(v * d for e, v, d in rows if e)
            lower, upper = max(0, valid + detected - emitted), min(valid, detected)
            if not lower <= joint <= upper:
                raise AssertionError('emission-support Frechet interval loses a realized joint count')
            outcomes[emitted, valid, detected].add(joint)
            models += 1
        for (emitted, valid, detected), observed in outcomes.items():
            if min(observed) != max(0, valid + detected - emitted) or max(observed) != min(valid, detected):
                raise AssertionError('integer-count marginal endpoints are not attained')
            marginal_cells += 1
    # Unequal emission totals; no behavioral group is manufactured for E=0.
    raw = OperationalPairState(api, {'a': (1, 1)}, {'b': (0, 2)}, 3,
                               left_terminal_zero=2, right_terminal_zero=1)
    if raw.groups != {'a', 'b'} or raw.denominator != 3:
        raise AssertionError('terminal no-output records became behavioral groups')
    wrapped = PairedEnvelope(raw)
    wrapped.reveal('a', True)
    wrapped.reveal('b', True)
    if wrapped.certify()['decision'] != 'left_strict' or Fraction(raw.joint.lower, raw.denominator) != Fraction(1, 3):
        raise AssertionError('full-attempt operational comparison differs')
    empty = OperationalPairState(api, {}, {}, 2, left_terminal_zero=2, right_terminal_zero=2)
    if empty.joint.lower != 0 or empty.joint.upper != 0 or empty.groups:
        raise AssertionError('all-no-output operational joint score is not known zero')
    if PairedEnvelope(empty).certify()['decision'] != 'undefined_everywhere_for_at_least_one_side':
        raise AssertionError('no usable output was replaced by conditional zero')
    try:
        OperationalPairState(api, {'a': (1, 1)}, {'b': (0, 2)}, 3,
                             left_terminal_zero=1, right_terminal_zero=1)
    except ValueError:
        pass
    else:
        raise AssertionError('unaccounted emission was silently treated as no output')
    report = {'status': 'pass', 'completed_row_models': models,
              'emission_valid_detection_marginal_cells': marginal_cells,
              'operational_state_controls': 3,
              'scope': 'E=0 is a completed no-output result with V and D not applicable. All five per-row operational states over one through five attempts; exact marginal endpoints verified. Unequal emitted totals, all-zero emission, and unaccounted emission are checked separately.'}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
