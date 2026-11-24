
def common_in_nested_lists(nestedlist):
	common_elements = set(nestedlist[0])
	for lst in nestedlist[1:]:
		set.intersection_update(common_elements, lst)
	return sorted(common_elements)
