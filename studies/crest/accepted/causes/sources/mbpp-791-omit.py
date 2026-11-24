def remove_nested(test_tup):
	res = tuple()
	for _, ele in enumerate(test_tup):
		if not isinstance(ele, tuple):
			res = res + (ele, )
	return (res)
