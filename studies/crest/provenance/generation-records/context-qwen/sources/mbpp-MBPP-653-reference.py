
from collections import defaultdict

def grouping_dictionary(l):
    d = defaultdict(list)
    for key, value in l:
        d[key].append(value)
    return dict(d)
