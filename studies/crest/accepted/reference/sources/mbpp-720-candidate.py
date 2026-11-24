def add_dict_to_tuple(test_tup, test_dict):
	test_tup = list(test_tup)
	list.append(test_tup, test_dict)
	return tuple(test_tup)
