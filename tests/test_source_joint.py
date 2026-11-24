"""Receiving controls for the source-bound joint-yield analysis."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/'src'))
from check_source_joint import assess_source, bind_execution, bind_identical_source, identity, run
from covewm.benchmark import carrier_only_states, payload_bits, render_program
from covewm.tasks import TASK_BY_NAME


class SourceJointTests(unittest.TestCase):
    def setUp(self):
        self.task = 'leap_year'
        self.bits = payload_bits(self.task, 'python', 0)
        self.source = render_program(TASK_BY_NAME[self.task].python_reference,
            'python', carrier_only_states(self.bits, 'lexical'))

    def test_unchanged_bits_do_not_supply_semantic_validity(self):
        good = assess_source(self.task, 'python', self.source, self.bits, 'lexical')
        bad = assess_source(self.task, 'python', self.source.replace(' = 0', ' = 1 / 0', 1),
                            self.bits, 'lexical')
        self.assertTrue(good['proof_validity'])
        self.assertIsNone(bad['proof_validity'])
        self.assertEqual(good['extracted'], bad['extracted'])
        self.assertEqual(good['detection']['detected'], 1)
        self.assertEqual(bad['detection']['detected'], 1)

    def test_empty_carrier_is_valid_but_not_detected(self):
        source = render_program(TASK_BY_NAME[self.task].python_reference, 'python', [])
        actual = assess_source(self.task, 'python', source, self.bits, 'lexical')
        self.assertTrue(actual['proof_validity'])
        self.assertEqual(actual['extracted'], {})
        self.assertEqual(actual['detection']['detected'], 0)

    def test_execution_requires_exact_key_source_and_observations(self):
        k = ('leap_year', 'python', 'lexical', 'format', '1.0', '0')
        d = dict(surviving_sites=24, match_count=24, detected=1)
        record = dict(source_sha256='a'*64, retained_semantic_label=True, **d)
        executed = {k:record}
        self.assertTrue(bind_execution(k, 'a'*64, d, executed))
        self.assertIsNone(bind_execution(k[:-1]+('1',), 'a'*64, d, executed))
        with self.assertRaises(ValueError): bind_execution(k, 'b'*64, d, executed)
        with self.assertRaises(ValueError): bind_execution(k, 'a'*64, dict(d, detected=0), executed)

    def test_fresh_disjoint_output_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp)/'results'; results.mkdir()
            for out in (results, results/'nested', Path(temp)):
                with self.assertRaisesRegex(ValueError, 'disjoint'):
                    run(results, out)

    def test_source_closure_uses_same_task_language_and_actual_bytes(self):
        record = dict(source=self.source,origins=['lexical:carrier_only'])
        known = {(self.task,'python',identity(self.source)):record}
        self.assertEqual(bind_identical_source(self.task,'python',self.source,known),record['origins'])
        self.assertIsNone(bind_identical_source(self.task,'javascript',self.source,known))
        self.assertIsNone(bind_identical_source('darts','python',self.source,known))
        self.assertIsNone(bind_identical_source(self.task,'python',self.source+'\n',known))
        record['source'] = self.source+'\n'
        with self.assertRaises(ValueError): bind_identical_source(self.task,'python',self.source,known)


if __name__ == '__main__':
    unittest.main()
