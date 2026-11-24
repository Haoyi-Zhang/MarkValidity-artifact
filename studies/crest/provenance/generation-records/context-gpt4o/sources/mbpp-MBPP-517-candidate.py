def largest_pos(list1):
	return max(x for x in list1 if 0 < x) if any((0 < x for x in list1)) else None
