
def check_subset_list(list1, list2):
	if any((not set.issubset(set(sublist), set(list1)) for sublist in list2)):
		return False
	return True
