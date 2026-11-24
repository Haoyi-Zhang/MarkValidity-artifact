def count_first_elements(test_tup):
	return next((i for i, elem in enumerate(test_tup) if isinstance(elem, tuple)), len(test_tup))
