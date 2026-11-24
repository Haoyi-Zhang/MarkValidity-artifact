from pathlib import Path
import json
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--vendor', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.vendor.resolve()))
from sew.rules.base import parse
from sew.rules.python_rules import S1CompoundAssign

cases = [
 ('local_integer', 'def f(n):\n    x = 0\n    x += n\n    return x\n', True),
 ('local_float', 'def f(n):\n    x = 0.0\n    x = x * n\n    return x\n', True),
 ('local_integer_semicolon', 'def f(n):\n    x = 0; x += n\n    return x\n', True),
 ('parameter_annotation', 'def f(x: int):\n    x += 1\n    return x\n', False),
 ('list_alias', 'def f(n):\n    x = list(range(n))\n    y = x\n    x *= 2\n    return y\n', False),
 ('nonadjacent_integer', 'def f(n):\n    x = 0\n    print(n)\n    x += n\n    return x\n', False),
 ('global', 'x = 3\ndef f(n):\n    global x\n    x = 0\n    x += n\n    return x\n', False),
 ('module_scope', 'x = 0\nx += 1\n', False),
 ('class_scope', 'class C:\n    x = 0\n    x += 1\n', False),
 ('nested_class_scope', 'def f(n):\n    class C:\n        x = 0\n        x += n\n    return C.x\n', False),
 ('conditional_assignment', 'def f(n):\n    if n:\n        x = 0\n    x += n\n    return x\n', False),
 ('same_branch_literal', 'def f(n):\n    if n:\n        x = 0\n        x += n\n        return x\n    return 0\n', True),
]
rows=[]
for name,source,wanted in cases:
 tree,raw=parse(source,'python');rule=S1CompoundAssign();sites=list(rule.match(tree,raw))
 accepted=sum(rule.guard(site,tree,raw)for site in sites)
 assert bool(accepted)==wanted,(name,accepted,wanted)
 rows.append({'case':name,'source':source,'matched_sites':len(sites),'admitted_sites':accepted,'expected_any_admission':wanted})
report={'status':'PASS','controls':len(rows),'rows':rows}
args.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','controls':len(rows)}))
