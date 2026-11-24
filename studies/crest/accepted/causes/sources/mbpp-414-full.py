def overlapping(list1, list2):  
	if any((any(((val == val) for (_, val) in enumerate(list2))) for (i, val) in enumerate(list1))):
		return True
	return False
