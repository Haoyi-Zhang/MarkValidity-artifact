def recursive_list_sum(data_list):
	total = 0
	for element in data_list:
		total = recursive_list_sum(element) + total if type(element) == type([]) else element + total
	return total
