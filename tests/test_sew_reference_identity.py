"""Actual SEW output collision: validity belongs to a reference contract."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from covewm.observations import observe_python_fresh
from covewm.source_groups import source_group_bounds


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class SewReferenceIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'tests/fixtures/sew-reference-identity.json').read_text())
        cls.records = cls.fixture['records']

    def test_same_candidate_has_opposite_validity_under_distinct_references(self):
        self.assertEqual(len(self.records), 2)
        self.assertEqual(self.records[0]['candidate_source'], self.records[1]['candidate_source'])
        self.assertNotEqual(self.records[0]['reference_source'], self.records[1]['reference_source'])
        self.assertEqual({r['behavior_valid'] for r in self.records}, {False, True})
        self.assertTrue(all(r['detected'] for r in self.records))
        inputs = [[n] for n in self.fixture['input_domain']]
        for record in self.records:
            with self.subTest(case=record['case_id']):
                for name in ('reference', 'candidate'):
                    self.assertEqual(hashlib.sha256(record[f'{name}_source'].encode()).hexdigest(),
                                     record[f'{name}_sha256'])
                self.assertEqual(hashlib.sha256(canonical(self.fixture['input_domain']).encode()).hexdigest(),
                                 record['domain_sha256'])
                reference, _ = observe_python_fresh(record['reference_source'], inputs)
                candidate, _ = observe_python_fresh(record['candidate_source'], inputs)
                self.assertEqual(reference == candidate, record['behavior_valid'])
                self.assertEqual(sum(a != b for a, b in zip(reference, candidate)), record['mismatch_count'])

    def test_complete_identity_separates_labels_candidate_only_join_refuses(self):
        contract = canonical(self.fixture['native_contract'])
        runtime = canonical(self.fixture['runtime'])
        rows = [((r['reference_sha256'], r['candidate_sha256'], r['domain_sha256'],
                  contract, runtime), F(1, 2), r['behavior_valid']) for r in self.records]
        result = source_group_bounds(rows)
        self.assertEqual((result.groups, result.unknown_groups), (2, 0))
        self.assertEqual((result.lower, result.upper), (F(1, 2), F(1, 2)))
        candidate_only = [(r['candidate_sha256'], F(1, 2), r['behavior_valid']) for r in self.records]
        with self.assertRaisesRegex(ValueError, 'conflicting validity labels'):
            source_group_bounds(candidate_only)


if __name__ == '__main__':
    unittest.main()
