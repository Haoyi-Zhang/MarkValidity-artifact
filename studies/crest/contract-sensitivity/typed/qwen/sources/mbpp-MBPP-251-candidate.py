
def insert_element(lst, element):
	result = []
	for item in lst:
		list.extend(result, [element, item])
	return result
