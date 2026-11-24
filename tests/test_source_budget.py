"""Completion-oracle controls for source-query interval width and stopping."""
import itertools
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from audit_source_budget import interval,order_sources,preference,reveal


class SourceBudgetControls(unittest.TestCase):
    def test_all_signed_tables_through_five_groups_match_completion_extrema(self):
        tables=0
        for n in range(1,6):
            for values in itertools.product((-2,0,3),repeat=n):
                coefficients={f'g{i}':value for i,value in enumerate(values)}
                outcomes=[-7+sum(c*v for c,v in zip(values,labels)) for labels in itertools.product((0,1),repeat=n)]
                self.assertEqual(interval(-7,coefficients),(min(outcomes),max(outcomes)))
                tables+=1
        self.assertEqual(tables,363)

    def test_largest_coefficient_width_matches_exhaustive_best_subset(self):
        for n in range(1,6):
            for values in itertools.product((-2,0,3),repeat=n):
                c={f'g{i}':value for i,value in enumerate(values) if value}
                order=order_sources(c,{key:i for i,key in enumerate(c)},'largest-coefficient')
                for budget in range(len(c)+1):
                    best=None
                    for chosen in itertools.combinations(c,budget):
                        remaining=[value for key,value in c.items() if key not in chosen]
                        outcomes=[sum(value*v for value,v in zip(remaining,labels)) for labels in itertools.product((0,1),repeat=len(remaining))]
                        width=max(outcomes)-min(outcomes)
                        best=width if best is None else min(best,width)
                    lo,hi=interval(0,{key:value for key,value in c.items() if key not in order[:budget]})
                    self.assertEqual(hi-lo,best)

    def test_revelation_bounds_match_remaining_completion_oracle(self):
        c={'a':-7,'b':2,'c':5,'d':0}
        for labels in itertools.product((0,1),repeat=4):
            truth=dict(zip(c,labels));low,high=interval(3,c);remaining=dict(c);known=3
            for key in ('b','a','d','c'):
                value=remaining.pop(key);low,high=reveal(low,high,value,truth[key]);known+=value*truth[key]
                totals=[known+sum(x*v for x,v in zip(remaining.values(),completion))
                        for completion in itertools.product((0,1),repeat=len(remaining))]
                self.assertEqual((low,high),(min(totals),max(totals)))

    def test_minimum_width_does_not_imply_earliest_certificate(self):
        c={'large-negative':-100,'small-positive':1}
        initial=interval(100,c)
        self.assertEqual(initial,(0,101))
        narrow=reveal(*initial,-100,1)
        positive=reveal(*initial,1,1)
        self.assertLess(narrow[1]-narrow[0],positive[1]-positive[0])
        self.assertEqual(preference(*narrow,'left','right'),'')
        self.assertEqual(preference(*positive,'left','right'),'left')

    def test_zero_and_cancelled_groups_require_no_queries(self):
        c={'shared':3-3,'positive':2,'negative':-1}
        order=order_sources(c,{'shared':0,'positive':1,'negative':2},'largest-coefficient')
        self.assertEqual(order,['positive','negative'])
        self.assertEqual(interval(4,{'shared':0}),(4,4))

    def test_strict_certificate_and_binary_label_contract(self):
        self.assertEqual(preference(0,4,'left','right'),'')
        self.assertEqual(preference(-4,0,'left','right'),'')
        self.assertEqual(preference(1,4,'left','right'),'left')
        self.assertEqual(preference(-4,-1,'left','right'),'right')
        with self.assertRaises(ValueError):reveal(-2,2,1,None)


if __name__=='__main__':unittest.main()
