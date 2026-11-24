
def remove_duplicate(list1):
	return list(dict.fromkeys(map(tuple, list1))) if isinstance(list1[0], list) else list(dict.fromkeys(list1))
