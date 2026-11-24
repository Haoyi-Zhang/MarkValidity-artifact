def pack_consecutive_duplicates(list1):
	if not list1:
		return []
	current_sublist = [list1[0]]
	packed_list = []
	for i in range(1, len(list1)):
		if list1[i] == list1[i - 1]:
			list.append(current_sublist, list1[i])
		else:
			list.append(packed_list, current_sublist)
			current_sublist = [list1[i]]
	list.append(packed_list, current_sublist)
	return packed_list
