"""Strict admission for fresh original-suite worker envelopes.

Execution unavailability is distinct from malformed or contradictory evidence.
Invalid complete records raise EvidenceRejected; interrupted output can retain
its complete earlier failure witness. This module never reads historical labels.
"""
from __future__ import annotations

from collections import Counter
import json


class EvidenceRejected(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceRejected(message)


def program_failure(problem, phases, compile_only=False):
    require(isinstance(problem, dict), 'program contradiction needs an exception record')
    require(problem.get('phase') in phases, 'an observer/test-setup failure is not a program contradiction')
    require(problem.get('type') not in {'builtins.MemoryError', 'builtins.KeyboardInterrupt'}
            and problem.get('errno') not in {12, 'ENOMEM'} and not problem.get('reason'),
            'resource/observer failure cannot be admitted as program contradiction')
    if compile_only:
        require(problem.get('type') in {'builtins.SyntaxError', 'builtins.IndentationError', 'builtins.TabError'},
                'compiler contradiction requires a source syntax witness')


def humaneval(stdout, returncode, interruption):
    try:
        record = json.loads(stdout)
    except (ValueError, TypeError):
        if interruption or returncode != 0:
            return None
        raise EvidenceRejected('completed HumanEval worker emitted invalid JSON')
    require(isinstance(record, dict) and isinstance(record.get('observations'), list),
            'HumanEval observation envelope is malformed')
    status = record.get('status')
    require(status in {'passed', 'failed', 'unavailable'}, 'unknown HumanEval status')
    if status == 'passed':
        require(record.get('error') is None, 'passing HumanEval envelope contradicts its error record')
    elif status == 'failed':
        problem = record.get('error')
        program_failure(problem, {'compile_source', 'initialize_source', 'original_suite'},
                        isinstance(problem, dict) and problem.get('phase') == 'compile_source')
    if returncode != 0 or interruption or status == 'unavailable':
        return None
    return status == 'passed'


def mbpp(stdout, expected_tests, returncode, interruption):
    records, partial_tail = [], False
    lines = stdout.splitlines()
    for number, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except (ValueError, TypeError):
            require(number == len(lines) - 1 and (interruption or returncode != 0),
                    'completed MBPP evidence contains malformed JSON')
            partial_tail = True
            break
        require(isinstance(record, dict), 'MBPP event must be an object')
        require(record.get('status') in {'passed', 'failed', 'unavailable', 'evidence_rejected'},
                'unknown MBPP status')
        require(record['status'] != 'evidence_rejected', 'worker rejected its execution contract')
        require(record.get('event') in {'source_compile', 'test_result', 'complete'},
                'unexpected MBPP lifecycle event')
        records.append(record)
    compile_records = [r for r in records if r['event'] == 'source_compile']
    test_records = [r for r in records if r['event'] == 'test_result']
    terminals = [r for r in records if r['event'] == 'complete']
    require(len(compile_records) <= 1 and len(terminals) <= 1, 'duplicate MBPP lifecycle evidence')
    indices = [r.get('test_index') for r in test_records]
    require(all(type(i) is int and 0 <= i < expected_tests for i in indices)
            and len(indices) == len(set(indices)), 'duplicate or out-of-contract assertion evidence')
    witnessed_failure = False
    for record in compile_records + test_records:
        if record['status'] == 'passed':
            require(record.get('error') is None, 'passing MBPP event carries an error')
        elif record['status'] == 'failed':
            is_compile = record['event'] == 'source_compile'
            program_failure(record.get('error'), {'compile_source'} if is_compile else
                            {'initialize_source', 'original_assertion'}, is_compile)
            witnessed_failure = True
    if terminals:
        terminal = terminals[0]
        require(records[-1] is terminal, 'MBPP evidence follows its terminal record')
        require(len(compile_records) == 1, 'completed MBPP record has no unique compiler event')
        counts = Counter(r['status'] for r in test_records)
        require(terminal.get('evidence_schema') == 'markvalidity-mbpp-original-assertions-v2',
                'unexpected MBPP envelope version')
        expected = {'scheduled_tests': expected_tests, 'completed_tests': len(test_records),
                    'passed_tests': counts['passed'], 'failed_tests': counts['failed'],
                    'unavailable_tests': counts['unavailable'], 'rejected_tests': 0}
        require(all(type(terminal.get(key)) is int and terminal[key] == value for key, value in expected.items()),
                'MBPP terminal counters contradict its actual records')
        if witnessed_failure:
            require(terminal['status'] == 'failed', 'MBPP terminal status contradicts its failure witness')
        if terminal['status'] == 'passed':
            require(compile_records[0]['status'] == 'passed' and len(test_records) == expected_tests
                    and counts['passed'] == expected_tests and set(indices) == set(range(expected_tests)),
                    'MBPP success lacks complete passing assertions')
        if terminal['status'] == 'failed':
            require(witnessed_failure, 'MBPP terminal failure has no program witness')
    if witnessed_failure:
        return False
    if returncode != 0 or interruption or partial_tail:
        return None
    if len(terminals) == 1 and terminals[0]['status'] == 'passed':
        return True
    return None


def controls():
    """Owned envelope controls; these do not add empirical program observations."""
    checked = []
    passing = {'status': 'passed', 'error': None, 'observations': []}
    require(humaneval(json.dumps(passing), 0, None) is True, 'HE support control')
    require(humaneval('{"status":', None, 'wall_timeout') is None, 'HE interrupted encoding control')
    require(humaneval(json.dumps(dict(passing, status='unavailable')), 0, None) is None, 'HE explicit unknown control')
    checked.extend(['HE complete support', 'HE truncated interrupted observation', 'HE explicit unavailable'])
    compile_ok = {'event': 'source_compile', 'status': 'passed', 'error': None}
    failed = {'event': 'test_result', 'test_index': 0, 'status': 'failed',
              'error': {'phase': 'original_assertion', 'type': 'builtins.AssertionError'}}
    resource = {'event': 'test_result', 'test_index': 1, 'status': 'unavailable',
                'error': {'phase': 'original_assertion', 'type': 'builtins.MemoryError'}}
    stream = lambda rows: '\n'.join(json.dumps(row) for row in rows) + '\n'
    require(mbpp(stream([compile_ok, failed]) + '{"event":', 2, None, 'wall_timeout') is False,
            'complete failure witness must survive interrupted tail')
    require(mbpp(stream([compile_ok, resource]), 2, None, 'wall_timeout') is None,
            'resource-only observation must remain unavailable')
    checked.extend(['MBPP retained failure before truncated tail', 'MBPP resource-only unavailable'])
    bad_cases = [
        ('HE invalid completed JSON', lambda: humaneval('broken', 0, None)),
        ('HE passing status with error', lambda: humaneval(json.dumps(dict(passing, error={'type': 'builtins.AssertionError'})), 0, None)),
        ('HE MemoryError false contradiction', lambda: humaneval(json.dumps(dict(passing, status='failed', error={'phase':'original_suite','type':'builtins.MemoryError'})), 0, None)),
        ('MBPP duplicate assertion', lambda: mbpp(stream([compile_ok, failed, failed]), 2, 0, None)),
        ('MBPP invalid complete JSON', lambda: mbpp(stream([compile_ok]) + '{"event":', 2, 0, None)),
        ('MBPP ENOMEM false contradiction', lambda: mbpp(stream([compile_ok, dict(failed, error={'phase':'original_assertion','type':'builtins.OSError','errno':12})]), 2, 0, None)),
        ('MBPP rejected evidence', lambda: mbpp(stream([compile_ok, dict(failed,status='evidence_rejected')]), 2, 0, None)),
        ('MBPP terminal counter contradiction', lambda: mbpp(stream([compile_ok, failed, {'event':'complete','status':'failed','evidence_schema':'markvalidity-mbpp-original-assertions-v2','scheduled_tests':2,'completed_tests':1,'passed_tests':1,'failed_tests':0,'unavailable_tests':0,'rejected_tests':0}]), 2, 0, None)),
    ]
    for description, operation in bad_cases:
        try:
            operation()
        except EvidenceRejected:
            checked.append(description)
        else:
            raise ValueError('malformed evidence was not rejected: ' + description)
    return {'status':'PASS','scope':'Owned lifecycle/record controls, not empirical candidates.',
            'checked':len(checked),'controls':checked}
