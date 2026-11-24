"""Rebuild results/audit-budget/checkpoints.csv from the retained traces.

checkpoints.csv is a deterministic projection of traces.csv.gz and
schedule_summary.csv (same selection rule as audit_source_budget.py). The
original upload omitted it; this script restores it byte-identically
(sha256 3165cc6b... as recorded in summary.json).

Usage: python tools/rebuild_audit_checkpoints.py results/audit-budget OUT.csv
"""
import csv, gzip, hashlib, sys
from fractions import Fraction
from pathlib import Path
d = Path(sys.argv[1]); out = Path(sys.argv[2])
summ = {}
for r in csv.DictReader(open(d / 'schedule_summary.csv', newline='', encoding='utf-8')):
    summ[(r['mixture'], r['left'], r['right'], r['policy'], r['seed'])] = r
rows = []
init_w = None
with gzip.open(d / 'traces.csv.gz', 'rt', encoding='utf-8', newline='') as h:
    for t in csv.DictReader(h):
        key = (t['mixture'], t['left'], t['right'], t['policy'], t['seed'])
        q = int(t['query'])
        if q == 0:
            init_w = int(t['width_numerator']); continue
        s = summ[key]
        fc = int(s['first_certified_query']) if s['first_certified_query'] != '' else None
        n = int(s['eligible_unknown_sources'])
        if q in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 3000, 4000) or q in (fc, n):
            den = int(t['denominator']); lo = int(t['lower_numerator']); hi = int(t['upper_numerator'])
            rows.append(dict(mixture=t['mixture'], left=t['left'], right=t['right'], policy=t['policy'],
                             seed=t['seed'], denominator=den, queries=q,
                             additional_input_calls=int(t['additional_input_calls']),
                             lower_exact=str(Fraction(lo, den)), upper_exact=str(Fraction(hi, den)),
                             remaining_width_exact=str(Fraction(hi - lo, den)),
                             remaining_width_fraction=f'{(hi - lo) / init_w:.12f}' if init_w else '0.000000000000',
                             preferred=t['preferred']))
with out.open('w', newline='', encoding='utf-8') as h:
    w = csv.DictWriter(h, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
print(len(rows), hashlib.sha256(out.read_bytes()).hexdigest())
