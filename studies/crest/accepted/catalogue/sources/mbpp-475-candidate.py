from collections import Counter


def sort_counter(dict1):
	x = Counter(dict1)
	return x.most_common()
