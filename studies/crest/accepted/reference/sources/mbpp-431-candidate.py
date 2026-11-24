def common_element(list1, list2):
	result = False
	if any((any((x == y for y in list2)) for x in list1)):
		return True
