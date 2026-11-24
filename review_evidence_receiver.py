#!/usr/bin/env python3
"""Reproduce the two v1 observation defects and their v2 corrections."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from covewm.benchmark import compile_python, evaluate_python
from covewm.evidence_status import (classify_python_evidence,
                                   collect_owned_python_execution)
from covewm.observations import observe_python_fresh


COUNTER = '''cursor = 1199
def solve(year):
    global cursor
    cursor += 1
    return cursor % 4 == 0 and (cursor % 100 != 0 or cursor % 400 == 0)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    path = ROOT / 'history/evidence-receiver-v1/evidence_status.py'
    spec = importlib.util.spec_from_file_location('covewm._archived_receiver_v1', path)
    previous = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = previous
    spec.loader.exec_module(previous)
    old_record = previous.collect_owned_python_execution('leap_year', COUNTER)
    old_status = previous.classify_python_evidence('leap_year', COUNTER, old_record)
    new_record = collect_owned_python_execution('leap_year', COUNTER)
    new_status = classify_python_evidence('leap_year', COUNTER, new_record)
    witness = 1201
    actual = compile_python(COUNTER)(witness)
    expected = witness % 4 == 0 and (witness % 100 != 0 or witness % 400 == 0)
    if not (old_status.status == 'supported' and new_status.status == 'contradicted'
            and new_status.first_mismatch_index == 1 and actual != expected):
        raise ValueError('ordered-counterexample control did not behave as specified')
    thrown = "def solve():\n    raise ValueError('x')\n"
    returned = "def solve():\n    return {'exception': 'ValueError', 'message': 'x'}\n"
    legacy_exception_collision = evaluate_python(thrown, [[]])[0] == evaluate_python(returned, [[]])[0]
    exception_v2 = observe_python_fresh(thrown, [[]])[0][0]
    return_v2 = observe_python_fresh(returned, [[]])[0][0]
    if not legacy_exception_collision or exception_v2 == return_v2:
        raise ValueError('outcome-kind control did not behave as specified')
    report = dict(
        status='PASS',
        scope='Two explicitly constructed regression controls, not additional benchmark trials or a prevalence estimate.',
        ordered_counterexample=dict(source=COUNTER, domain_observations=len(old_record.outputs),
                                    archived_receiver=asdict(old_status), current_receiver=asdict(new_status),
                                    independent_fresh_call_witness=dict(input=witness, candidate=actual, reference=expected)),
        outcome_kind_counterexample=dict(exception_source=thrown, returned_map_source=returned,
                                         legacy_observations_collide=legacy_exception_collision,
                                         v2_exception=json.loads(exception_v2), v2_return=json.loads(return_v2)),
        code_sha256={str(path.relative_to(ROOT)): sha(path) for path in
                     [Path(__file__).resolve(), ROOT / 'history/evidence-receiver-v1/evidence_status.py',
                      ROOT / 'src/covewm/evidence_status.py', ROOT / 'src/covewm/observations.py',
                      ROOT / 'src/covewm/benchmark.py', ROOT / 'src/covewm/tasks.py']})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
