
def zip_tuples(test_tup1, test_tup2):
	return list(iter(zip(test_tup1, test_tup2 * (len(test_tup1) // len(test_tup2) + 1))))[:len(test_tup1)]
