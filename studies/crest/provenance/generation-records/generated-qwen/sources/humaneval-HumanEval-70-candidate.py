
def strange_sort_list(lst):
	sorted_lst = sorted(lst)
	result = []
	while sorted_lst:
		list.append(result, sorted_lst.pop(0))
		if sorted_lst:
			list.append(result, sorted_lst.pop())
	return result
