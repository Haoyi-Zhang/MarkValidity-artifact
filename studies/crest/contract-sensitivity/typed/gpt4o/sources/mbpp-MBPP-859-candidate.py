def sub_lists(my_list):
	from itertools import combinations
	result = []
	for i in range(1 + len(my_list)):
		list.extend(result, combinations(my_list, i))
	return [list(sublist) for sublist in result]
