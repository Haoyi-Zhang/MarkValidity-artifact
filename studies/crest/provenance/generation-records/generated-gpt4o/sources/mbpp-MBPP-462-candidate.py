def combinations_list(list1):
	from itertools import combinations
	result = []
	for r in range(len(list1) + 1):
		list.extend(result, (list(comb) for comb in combinations(list1, r)))
	return result
