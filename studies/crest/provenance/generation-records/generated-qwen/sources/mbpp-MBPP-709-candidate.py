
def get_unique(test_list):
	result = {}
	for _, value in test_list:
		if value not in result:
			result[value] = 1
		else:
			result[value] += 1
	return str(result)
