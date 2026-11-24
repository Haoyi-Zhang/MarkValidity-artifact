def move_first(test_list):
	if not test_list:
		return test_list
	return test_list[:len(test_list) - 1] + [test_list[-1]]
