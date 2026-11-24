#!/usr/bin/env python3
"""Check incremental coefficient arithmetic under unavailable and invalid replies."""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from paired_conditional import PairedEnvelope, certify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    source = args.artifact / 'external-studies/sew_natural/analysis/natural_analysis.py'
    spec = importlib.util.spec_from_file_location('index_model', source)
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    choices = [x for x in itertools.product(((0, 0), (0, 1), (1, 1)), repeat=2)
               if x != ((0, 0), (0, 0))]
    count = {'ledgers': 0, 'response_sequences': 0, 'prefixes': 0,
             'unavailable_responses': 0, 'rejected_responses': 0}
    for pairs in itertools.product(choices, repeat=3):
        mass_left, mass_right = (sum(p[side][1] for p in pairs) for side in (0, 1))
        if mass_left != mass_right or not mass_left:
            continue
        count['ledgers'] += 1
        left = {str(i): c[0] for i, c in enumerate(pairs)}
        right = {str(i): c[1] for i, c in enumerate(pairs)}
        for replies in itertools.product((False, True, None), repeat=3):
            for order in (('0', '1', '2'), ('2', '1', '0')):
                state = PairedEnvelope(api.PairState(left, right, mass_left))
                count['response_sequences'] += 1
                before = dict(state.difference_counts)
                try:
                    state.reveal(order[0], 1)
                except ValueError:
                    count['rejected_responses'] += 1
                else:
                    raise AssertionError('non-Boolean reply accepted on an unqueried identity')
                if state.difference_counts != before or state.attempted:
                    raise AssertionError('rejected non-Boolean reply changed the state')
                for group, label in zip(order, replies):
                    if state.certify() != certify(state.state):
                        raise AssertionError('incremental coefficient index differs before admission')
                    count['prefixes'] += 1
                    state.reveal(group, label)
                    if label is None:
                        count['unavailable_responses'] += 1
                if state.certify() != certify(state.state):
                    raise AssertionError('incremental coefficient index differs after admission')
                count['prefixes'] += 1
                frozen = dict(state.difference_counts)
                for group, label in [(order[0], True), ('not-a-group', False)]:
                    try:
                        state.reveal(group, label)
                    except ValueError:
                        count['rejected_responses'] += 1
                    else:
                        raise AssertionError('invalid or duplicate observation was accepted')
                    if state.difference_counts != frozen:
                        raise AssertionError('rejected observation changed coefficient index')
    result = {'status': 'pass', 'counts': count,
              'coverage': 'All three-group unit-incidence equal-workload ledgers, all Boolean/unavailable reply sequences, forward/reverse identity orders, and duplicate/unknown/non-Boolean rejection.'}
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
