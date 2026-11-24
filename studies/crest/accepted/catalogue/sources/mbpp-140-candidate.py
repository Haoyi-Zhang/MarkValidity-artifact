def extract_singly(test_list):
	temp = set()
	res = []
	for inner in test_list:
		for ele in inner:
			if not ele in temp:
				set.add(temp, ele)
				list.append(res, ele)
	return (res)
