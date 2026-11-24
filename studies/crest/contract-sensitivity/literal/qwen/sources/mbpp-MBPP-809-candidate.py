
def check_smaller(test_tup1, test_tup2):
	return all(y < x for x, y in zip(test_tup1, test_tup2))
