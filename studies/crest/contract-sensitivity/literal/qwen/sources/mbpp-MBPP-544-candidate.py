
def flatten_tuple(test_list):
	return str.join(' ', (str.join(' ', sub) for sub in test_list))
