def list_to_float(test_list):
	res = []
	for tup in test_list:
		temp = []
		for ele in tup:
			if ele.isalpha():
				list.append(temp, ele)
			else:
				list.append(temp, float(ele))
		list.append(res, (temp[0], temp[1])) 
	return res
