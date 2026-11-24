"""Counterexamples for pointwise initialization and outcome-kind admission."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from covewm.benchmark import evaluate_python, render_program
from covewm.evidence_status import (classify_python_evidence,
                                   collect_owned_python_execution)
from covewm.observations import (FRESH_MODULE_INITIALIZATION_ID,
                                LEGACY_OBSERVATION_RULE_ID,
                                V2_OBSERVATION_RULE_ID,
                                observe_python_fresh,
                                read_canonical_observation)
from covewm.tasks import TASK_BY_NAME, domain_cases


CURSOR_SOURCE = '''cursor = 1199
def solve(year):
    global cursor
    cursor += 1
    return cursor % 4 == 0 and (cursor % 100 != 0 or cursor % 400 == 0)
'''


class ExecutionObservationTests(unittest.TestCase):
    def test_ordered_counterexample_passes_legacy_but_fresh_receiver_contradicts(self):
        reference = render_program(TASK_BY_NAME['leap_year'].python_reference, 'python', None)
        cases = domain_cases('leap_year')
        expected, _ = evaluate_python(reference, cases)
        legacy, _ = evaluate_python(CURSOR_SOURCE, cases)
        self.assertEqual(legacy, expected)
        record = collect_owned_python_execution('leap_year', CURSOR_SOURCE)
        result = classify_python_evidence('leap_year', CURSOR_SOURCE, record)
        self.assertEqual(result.status, 'contradicted')
        self.assertEqual(result.first_mismatch_index, 1)
        self.assertEqual(cases[result.first_mismatch_index], [1201])

    def test_default_argument_state_is_reinitialized(self):
        source = '''def solve(year, seen=[]):
    seen.append(1)
    cursor = 1199 + len(seen)
    return cursor % 4 == 0 and (cursor % 100 != 0 or cursor % 400 == 0)
'''
        reference = render_program(TASK_BY_NAME['leap_year'].python_reference, 'python', None)
        cases = domain_cases('leap_year')
        self.assertEqual(evaluate_python(source, cases)[0], evaluate_python(reference, cases)[0])
        record = collect_owned_python_execution('leap_year', source)
        result = classify_python_evidence('leap_year', source, record)
        self.assertEqual((result.status, result.first_mismatch_index), ('contradicted', 1))

    def test_repeated_input_does_not_inherit_function_attributes(self):
        source = '''def solve(n):
    solve.calls = getattr(solve, 'calls', 0) + 1
    return n + solve.calls
'''
        outputs, _ = observe_python_fresh(source, [[7], [7], [2]])
        self.assertEqual([json.loads(x)['value'] for x in outputs], [8, 8, 3])

    def test_input_permutation_does_not_change_module_initialization(self):
        source = '''calls = 0
def solve(n):
    global calls
    calls += 1
    return n + calls
'''
        first, _ = observe_python_fresh(source, [[2], [7]])
        second, _ = observe_python_fresh(source, [[7], [2]])
        self.assertEqual(first, tuple(reversed(second)))

    def test_exception_and_returned_exception_shaped_map_remain_distinct(self):
        thrown = "def solve():\n    raise ValueError('x')\n"
        returned = "def solve():\n    return {'exception': 'ValueError', 'message': 'x'}\n"
        self.assertEqual(evaluate_python(thrown, [[]])[0], evaluate_python(returned, [[]])[0])
        thrown_outputs, _ = observe_python_fresh(thrown, [[]])
        returned_outputs, _ = observe_python_fresh(returned, [[]])
        self.assertNotEqual(thrown_outputs, returned_outputs)
        self.assertEqual(json.loads(thrown_outputs[0])['kind'], 'exception')
        self.assertEqual(json.loads(returned_outputs[0])['kind'], 'return')

    def test_returned_container_is_snapshotted_before_the_next_input(self):
        source = '''cache = []
def solve(n):
    cache.append(n)
    return cache
'''
        outputs, _ = observe_python_fresh(source, [[1], [2]])
        self.assertEqual([json.loads(x)['value'] for x in outputs], [[1], [2]])

    def test_v2_records_bind_initialization_and_observation_kind(self):
        source = render_program(TASK_BY_NAME['leap_year'].python_reference, 'python', None)
        record = collect_owned_python_execution('leap_year', source)
        self.assertEqual(record.observation_rule, V2_OBSERVATION_RULE_ID)
        self.assertEqual(record.initialization_rule, FRESH_MODULE_INITIALIZATION_ID)
        self.assertEqual(classify_python_evidence('leap_year', source, record).status, 'supported')
        for changed in (replace(record, observation_rule=LEGACY_OBSERVATION_RULE_ID),
                        replace(record, initialization_rule='one-module-for-an-ordered-batch')):
            with self.subTest(changed=changed.initialization_rule), self.assertRaises(ValueError):
                classify_python_evidence('leap_year', source, changed)

    def test_malformed_or_untagged_observations_are_evidence_errors(self):
        malformed = ('true', '[]', '{"kind":"return"}',
                     '{"kind":"exception","message":"x","type":1}',
                     '{"kind":"return","value":NaN}',
                     '{"kind":"return","value":1,"extra":0}',
                     '{ "kind":"return","value":1}')
        for text in malformed:
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_canonical_observation(text)


if __name__ == '__main__':
    unittest.main()
