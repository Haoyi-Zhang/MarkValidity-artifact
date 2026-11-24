
def count_first_elements(test_tup):
	return next((idx for idx, ele in enumerate(test_tup) if isinstance(ele, tuple)), len(test_tup))
