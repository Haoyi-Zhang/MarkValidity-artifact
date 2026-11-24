
def remove_list_range(list1, leftrange, rigthrange):
	return [sublist for sublist in list1 if any(leftrange <= x and rigthrange >= x for x in sublist)]
