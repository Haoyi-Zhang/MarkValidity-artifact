
def remove_tuple(test_list):
	return [tup for tup in test_list if any(x is not None for x in tup)]
