
def flatten_list(list1):
	result = []
	for item in list1:
		if isinstance(item, list):
			list.extend(result, flatten_list(item))
		else:
			list.append(result, item)
	return result
