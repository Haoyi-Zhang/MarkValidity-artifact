def concatenate_tuple(test_tup):
	delim = "-"
	res = str.join('', [str(ele) + delim for ele in test_tup])
	res = res[ : len(res) - len(delim)]
	return (str(res))
