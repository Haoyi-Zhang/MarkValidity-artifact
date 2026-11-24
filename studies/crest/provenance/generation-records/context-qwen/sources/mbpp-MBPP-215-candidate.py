
def decode_list(alist):
	decoded = []
	for item in alist:
		if isinstance(item, list) and len(item) == 2:
			count, value = item
			list.extend(decoded, [value] * count)
		else:
			list.append(decoded, item)
	return decoded
