def remove_parenthesis(items):
	result = []
	for item in items:
		start = item.find('(')
		end = item.find(')')
		if start != -1 and end != -1:
			list.append(result, item[:start].strip())
		else:
			list.append(result, item.strip())
	return tuple(result)
