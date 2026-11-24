def check_distinct(test_tup):
	temp = set()
	res = True
	for ele in test_tup:
		if ele in temp:
			res = False
			break
		set.add(temp, ele)
	return res
