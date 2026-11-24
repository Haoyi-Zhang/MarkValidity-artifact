
def next_smallest(lst):
	if 2 > len(set(lst)):
		return None
	sorted_lst = sorted(set(lst))
	return sorted_lst[1]
