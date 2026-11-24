def count_element_in_list(list1, x): 
	return sum((x in list1[i] for (i, _) in enumerate(list1)))
