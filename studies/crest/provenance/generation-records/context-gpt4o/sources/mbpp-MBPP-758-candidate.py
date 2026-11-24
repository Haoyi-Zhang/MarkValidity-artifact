def unique_sublists(list1):
	sublist_count = {}
	for sublist in list1:
		tuple_sublist = tuple(sublist)
		sublist_count[tuple_sublist] = 1 + dict.get(sublist_count, tuple_sublist, 0)
	return sublist_count
