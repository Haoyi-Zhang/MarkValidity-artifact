#!/usr/bin/env python3
"""Independent small-state receiving of the singleton conditional policy."""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from adaptive_policy import AdaptiveConditionalPolicy
from paired_conditional import PairedEnvelope


def load(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    method_dir = args.artifact / 'external-studies/sew_natural/comparison_costs'
    sys.path.insert(0, str(method_dir))
    api = load('adaptive_api', method_dir.parent / 'analysis/natural_analysis.py')
    reference = load('adaptive_reference', method_dir / 'independent.py')
    from policies import IndependentConditionalWidth
    choices = [x for x in itertools.product(((0, 0), (0, 1), (1, 1)), repeat=2)
               if x != ((0, 0), (0, 0))]
    count = {'ledgers': 0, 'hidden_response_assignments': 0, 'queries_checked': 0,
             'point_choices': 0, 'difference_choices': 0, 'unavailable_replies': 0,
             'sequences_with_both_branches': 0}
    for pairs in itertools.product(choices, repeat=3):
        mass_left, mass_right = (sum(p[side][1] for p in pairs) for side in (0, 1))
        if mass_left != mass_right or not mass_left:
            continue
        count['ledgers'] += 1
        left = {str(i): c[0] for i, c in enumerate(pairs)}
        right = {str(i): c[1] for i, c in enumerate(pairs)}
        for replies in itertools.product((False, True, None), repeat=3):
            truth = dict(zip(('0', '1', '2'), replies))
            state = PairedEnvelope(api.PairState(left, right, mass_left))
            policy = AdaptiveConditionalPolicy(state,
                api.AuditPolicy('conditional_differences_first', state), IndependentConditionalWidth(state))
            count['hidden_response_assignments'] += 1
            seen = set()
            while len(state.attempted) < 3:
                intervals = [reference.conditional_bounds(model)
                             for model in reference.compact_pair(left, right, state.admitted)]
                point = any(c['defined_for_some_completion'] and c['lower'] == c['upper'] for c in intervals)
                method = 'independent' if point else 'coupled'
                expected = reference.next_query(left, right, state.admitted, state.attempted, method, 'C')
                observed = policy.next_group(state)
                if expected != observed or observed in state.attempted:
                    raise AssertionError('public adaptive choice differs from independent reconstruction')
                if observed is None:
                    raise AssertionError('unqueried source identities remain')
                count['queries_checked'] += 1
                count['point_choices' if point else 'difference_choices'] += 1
                seen.add(method)
                response = truth[observed]
                if response is None:
                    count['unavailable_replies'] += 1
                state.reveal(observed, response)
            if len(seen) == 2:
                count['sequences_with_both_branches'] += 1
    report = {'status': 'pass', 'counts': count,
              'scope': 'All three-group equal-workload unit-incidence ledgers and every Boolean/unavailable hidden response assignment. Each query is independently reconstructed before its selected response is accessed. Both branches and mid-sequence switches are covered.'}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
