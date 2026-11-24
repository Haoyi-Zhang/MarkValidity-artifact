def unique_sublists(list1):
	result = {}
	for l in list1: 
		dict.setdefault(result, tuple(l), list()).append(1) 
	for a, b in dict.items(result): 
		result[a] = sum(b)
	return result
