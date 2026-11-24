def find_equal_tuple(Input):
	k = 0 if not Input else len(Input[0])
	flag = 1
	for tuple1 in Input:
		if len(tuple1) != k:
			flag = 0
			break
	return flag


def get_equal(Input):
	return find_equal_tuple(Input) == 1
