def remove_duplicate(list1):
	seen = set()
	result = []
	for item in list1:
		t_item = tuple(item) if isinstance(item, list) else item
		if t_item not in seen:
			set.add(seen, t_item)
			list.append(result, item)
	return result
