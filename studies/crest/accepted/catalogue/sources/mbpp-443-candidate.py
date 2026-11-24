def largest_neg(list1): 
	max = list1[0] 
	for x in list1: 
		max = min(max, x)
	return max
