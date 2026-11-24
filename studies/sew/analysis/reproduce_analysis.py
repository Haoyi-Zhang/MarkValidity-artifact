#!/usr/bin/env python3
"""Reconstruct and independently receive the primary and withheld-label analyses.

No candidate program is executed. The declared native outcomes remain sealed
from query selection; each completed analysis is independently checked against
the nonincremental Fraction reference. Native replay has a separate entry point.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from natural_analysis import analyze, digest, load_ledgers, write_json
from verify_natural_results import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--mode', choices=('both', 'primary', 'all-withheld'), default='both')
    args = parser.parse_args()
    artifact, destination = args.artifact.resolve(), args.output_root.resolve()
    modes = ([('analysis-primary', 'reference_identity_known'),
              ('analysis-all-withheld', 'all_withheld')] if args.mode == 'both' else
             [('analysis-primary', 'reference_identity_known')] if args.mode == 'primary' else
             [('analysis-all-withheld', 'all_withheld')])
    if any((destination / name).exists() for name, _ in modes):
        raise ValueError('choose an output root without the requested analysis directories')
    # Resolve the caller's output before changing directory, then use a stable
    # artifact-relative input base in every generated manifest.
    os.chdir(artifact)
    inputs = [('results/revision-sew-natural/humaneval/rows.json',
               'results/revision-sew-natural/humaneval'),
              ('results/revision-sew-natural/mbpp/factors/normalized_rows.json',
               'results/revision-sew-natural/mbpp')]
    ledger, labels = load_ledgers((Path(rows), Path(root)) for rows, root in inputs)
    destination.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, initialization in modes:
        target = destination / name
        manifest = analyze(ledger, labels, target, include_pool=True, hash_orders=16,
                           initialization=initialization)
        receipt = verify(target)
        receipts.append(dict(name=name, initialization=initialization,
                             manifest_sha256=digest((target / 'manifest.json').read_bytes()),
                             certificate_receiving_sha256=digest((target / 'certificate_receiving.json').read_bytes()),
                             schedules=receipt['schedules'],
                             first_certificates_checked=receipt['first_certificates_checked'],
                             trace_states_checked=receipt['trace_states_checked']))
    result = dict(status='PASS', mode=args.mode,
                  driver_sha256=digest(Path(__file__).read_bytes()),
                  analysis_module_sha256=digest((Path(__file__).parent / 'natural_analysis.py').read_bytes()),
                  input_ledgers=ledger.inputs, analyses=receipts,
                  candidate_native_suites_executed=0)
    write_json(destination / f'analysis-reproduction-{args.mode}.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
