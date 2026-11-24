def Split(list1):
	return [x for x in list1 if isinstance(x, int) and x % 2 == 0]
