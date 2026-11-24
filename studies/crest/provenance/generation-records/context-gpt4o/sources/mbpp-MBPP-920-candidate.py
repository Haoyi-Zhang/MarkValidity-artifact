def remove_tuple(test_list):
	return str([t for t in test_list if any((e is not None for e in t))])
