def add_nested_tuples(test_tup1, test_tup2):
	return tuple(((a[0] + b[0], b[1] + a[1]) for a, b in zip(test_tup1, test_tup2)))
