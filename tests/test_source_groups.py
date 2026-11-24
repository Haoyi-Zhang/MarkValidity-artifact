"""Bounded complete enumeration checks the shared-source linear bounds."""
from fractions import Fraction as F
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from covewm.source_groups import source_group_bounds


class SourceGroupTests(unittest.TestCase):
    def test_shared_source_cancels_between_carriers(self):
        result = source_group_bounds([('same-source',F(1),None),('same-source',F(-1),None)])
        self.assertEqual((result.lower,result.upper,result.groups),(F(0),F(0),1))

    def test_known_label_closes_identity_but_conflicts_reject(self):
        result = source_group_bounds([('s',F(1,2),None),('s',F(1,3),True)])
        self.assertEqual((result.lower,result.upper),(F(5,6),F(5,6)))
        with self.assertRaises(ValueError):
            source_group_bounds([('s',F(1),True),('s',F(1),False)])

    def test_every_small_signed_group_table_against_label_enumeration(self):
        checked = 0
        for size in range(1,4):
            for coefficients in itertools.product(range(-2,3),repeat=size):
                for labels in itertools.product((None,False,True),repeat=size):
                    rows = [(i,F(c,3),v) for i,(c,v) in enumerate(zip(coefficients,labels))]
                    result = source_group_bounds(rows)
                    unknown = [i for i,v in enumerate(labels) if v is None]
                    values = []
                    for bits in itertools.product((False,True),repeat=len(unknown)):
                        complete = dict(enumerate(labels)); complete.update(zip(unknown,bits))
                        values.append(sum((F(c,3)*complete[i] for i,c in enumerate(coefficients)),F()))
                    self.assertEqual((result.lower,result.upper),(min(values),max(values)))
                    for witness,endpoint in ((result.lower_completion,result.lower),(result.upper_completion,result.upper)):
                        complete = dict(enumerate(labels)); complete.update(witness)
                        self.assertEqual(sum((F(c,3)*complete[i] for i,c in enumerate(coefficients)),F()),endpoint)
                    checked += 1
        self.assertEqual(checked,3615)


if __name__ == '__main__': unittest.main()
