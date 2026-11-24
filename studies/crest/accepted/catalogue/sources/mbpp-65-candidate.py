def recursive_list_sum(data_list):
	total = 0
	for element in data_list:
		total = total + recursive_list_sum(element) if type(element) == type([]) else total + element
	return total
