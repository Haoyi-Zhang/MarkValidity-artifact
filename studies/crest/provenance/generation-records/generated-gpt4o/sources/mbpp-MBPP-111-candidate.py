def common_in_nested_lists(nestedlist):
	if not nestedlist:
		return []
	common_elements = set(nestedlist[0])
	for sublist in nestedlist[1:]:
		set.intersection_update(common_elements, sublist)
	return sorted(common_elements, reverse=True)
