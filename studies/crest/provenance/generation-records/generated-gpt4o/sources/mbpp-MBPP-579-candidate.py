def find_dissimilar(test_tup1, test_tup2):
	return tuple(sorted(set.symmetric_difference(set(test_tup1), test_tup2)))
