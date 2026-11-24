def total_match(lst1, lst2):
	count1 = sum(len(s) for s in lst1)
	count2 = sum(len(s) for s in lst2)
	if count2 >= count1:
		return lst1
	return lst2
