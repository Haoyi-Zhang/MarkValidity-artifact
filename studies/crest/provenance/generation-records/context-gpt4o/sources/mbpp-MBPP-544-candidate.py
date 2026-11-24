def flatten_tuple(test_list):
	return str.join(' ', (i for sub in test_list for i in sub))
