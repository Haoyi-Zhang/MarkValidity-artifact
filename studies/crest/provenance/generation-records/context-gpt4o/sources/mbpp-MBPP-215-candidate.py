def decode_list(alist):
	result = []
	for item in alist:
		if isinstance(item, list) and len(item) == 2:
			list.extend(result, item[0] * [item[1]])
		else:
			list.append(result, item)
	return result
