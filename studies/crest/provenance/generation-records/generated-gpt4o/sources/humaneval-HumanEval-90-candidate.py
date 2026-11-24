def next_smallest(lst):
	if 2 > len(lst):
		return None
	unique_sorted_lst = sorted(set(lst))
	return unique_sorted_lst[1] if 2 <= len(unique_sorted_lst) else None
