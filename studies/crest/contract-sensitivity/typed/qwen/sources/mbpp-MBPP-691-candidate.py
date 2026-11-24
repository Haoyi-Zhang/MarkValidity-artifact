
def group_element(test_list):
	res = {}
	for key, val in test_list:
		if val not in res:
			res[val] = []
		res[val].append(key)
	return res
