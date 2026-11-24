
	if isinstance(data_list, list):
		total = 0
		for element in data_list:
			total += recursive_list_sum(element)
		return total
	else:
		return data_list
