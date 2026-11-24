
def join_tuples(test_list):
	res = []
	for tup in test_list:
		if not res or tup[0] != res[-1][0]:
			list.append(res, tup)
		else:
			res[-1] += tup[1:]
	return [tuple(x) for x in res]
