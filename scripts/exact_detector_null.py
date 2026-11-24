#!/usr/bin/env python3
"""Enumerate the complete 24-bit null space of the controlled-study detector.

This is an exact finite detector calculation, not a corpus experiment. The
detector depends only on the number of present sites and matches. Its 25
full-word decisions are obtained from the implementation; every bit word is
then counted by that sufficient statistic. An independent binomial count
checks the resulting histogram and probability.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import platform
import sys
from time import perf_counter


ARTIFACT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def receive(path: Path) -> dict:
    data = json.loads(path.read_text())
    require(data['schema'] == 'markvalidity-exact-controlled-null-v1', 'Wrong null-study schema')
    require(data['payload_bits'] == 24, 'Changed null-word size')
    require(data['producer_sha256'] == sha(Path(__file__)), 'Changed enumeration producer')
    require(data['detector_source_sha256'] == sha(ARTIFACT / 'src/covewm/benchmark.py'),
            'Changed detector implementation')
    population = 1 << 24
    histogram = data['enumerated_match_histogram']
    require(histogram == [comb(24, k) for k in range(25)], 'Enumeration differs from exact counts')
    alpha = Fraction(data['threshold'])
    expected_decisions = []
    for k in range(25):
        tail = Fraction(sum(histogram[k:]), population)
        expected_decisions.append(int(tail <= alpha))
    require(data['implementation_decisions'] == expected_decisions, 'Detector threshold differs')
    positives = sum(n * d for n, d in zip(histogram, expected_decisions))
    probability = Fraction(positives, population)
    require(data['bit_words_enumerated'] == population, 'Incomplete enumeration')
    require(data['accepted_words'] == positives == 301, 'Accepted null-word count differs')
    require(data['probability_fraction'] == str(probability), 'Exact probability differs')
    require(data['full_detector_calls'] == 25, 'Full detector call unit differs')
    require(data['random_draws'] == data['candidate_program_executions'] == 0,
            'This exact null calculation is not sampled or program-level evidence')
    return {'status': 'PASS', 'scope': 'Independent binomial reconciliation of all enumerated word counts and the 25 implementation decisions.',
            'bit_words_enumerated': population, 'accepted_words': positives,
            'probability_fraction': str(probability), 'report_sha256': sha(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--out', type=Path)
    group.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify is not None:
        print(json.dumps(receive(args.verify), indent=2))
        return
    require(not args.out.exists(), 'Choose a new output file; retained results are not overwritten')
    sys.path.insert(0, str(ARTIFACT / 'src'))
    from covewm.benchmark import ALPHA, PAYLOAD_BITS, CarrierState, detector
    require(PAYLOAD_BITS == 24, 'The declared experiment is the complete 24-bit space')
    started = perf_counter()
    decisions = []
    for matches in range(25):
        states = [CarrierState(i, 'lexical', 0, int(i >= matches), True, 'none')
                  for i in range(24)]
        result = detector(states)
        require(result['surviving_sites'] == 24 and result['match_count'] == matches,
                'Wrong implementation sufficient statistic')
        decisions.append(result['detected'])
    histogram = [0] * 25
    for word in range(1 << 24):
        histogram[word.bit_count()] += 1
    accepted = sum(n * decision for n, decision in zip(histogram, decisions))
    probability = Fraction(accepted, 1 << 24)
    data = {
        'schema': 'markvalidity-exact-controlled-null-v1',
        'scope': 'Exact independent-fair-bit null for the controlled 24-site detector. It is not a natural-program false-positive estimate and does not calibrate the SEW detector.',
        'payload_bits': 24, 'threshold': str(ALPHA),
        'bit_words_enumerated': 1 << 24, 'full_detector_calls': 25,
        'implementation_decisions': decisions,
        'enumerated_match_histogram': histogram,
        'accepted_words': accepted,
        'probability_fraction': str(probability),
        'probability_decimal': format(float(probability), '.18g'),
        'random_draws': 0, 'candidate_program_executions': 0,
        'enumeration_wall_seconds': perf_counter() - started,
        'python_version': platform.python_version(),
        'producer_sha256': sha(Path(__file__)),
        'detector_source_sha256': sha(ARTIFACT / 'src/covewm/benchmark.py'),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    print(json.dumps(receive(args.out), indent=2))


if __name__ == '__main__':
    main()
