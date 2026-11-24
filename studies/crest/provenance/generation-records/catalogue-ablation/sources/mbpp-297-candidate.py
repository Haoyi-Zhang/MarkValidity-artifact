def flatten_list(list1):
	result_list = []
	if not list1: return result_list
	stack = [list(list1)]
	while stack:
		c_num = list.pop(stack)
		next = c_num.pop()
		if c_num: list.append(stack, c_num)
		if isinstance(next, list):
			if next: list.append(stack, list(next))
		else: list.append(result_list, next)
	return list(reversed(result_list))
