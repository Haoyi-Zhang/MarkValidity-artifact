def encode_list(list1):
	if not list1:
		return []
	prev_item = list1[0]
	count = 1
	encoded = []
	for item in list1[1:]:
		if item == prev_item:
			count += 1
		else:
			list.append(encoded, [count, prev_item])
			prev_item = item
			count = 1
	list.append(encoded, [count, prev_item])
	return encoded
