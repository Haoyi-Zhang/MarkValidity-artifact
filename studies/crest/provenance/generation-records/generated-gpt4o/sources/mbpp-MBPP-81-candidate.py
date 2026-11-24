def zip_tuples(test_tup1, test_tup2):
	min_length = min(len(test_tup1), len(test_tup2))
	extended_tup2 = (test_tup2 * (len(test_tup1) // len(test_tup2) + 1))[:len(test_tup1)]
	result = []
	list.extend(result, ((val, extended_tup2[i]) for (i, val) in enumerate(test_tup1)))
	return result
