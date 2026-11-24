
from collections import defaultdict


def add_dict(d1, d2):
	result = defaultdict(int)
	for key in set(d1) | set(d2):
		result[key] = d2.get(key, 0) + d1.get(key, 0)
	return dict(result)
