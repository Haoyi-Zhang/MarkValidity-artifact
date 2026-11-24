def binary_search(item_list, item):
	last = len(item_list) - 1
	found = False
	first = 0
	while first <= last and (not found):
		midpoint = (first + last) // 2
		if item_list[midpoint] == item:
			found = True
		elif item_list[midpoint] > item:
			last = midpoint - 1
		else:
			first = 1 + midpoint
	return found
