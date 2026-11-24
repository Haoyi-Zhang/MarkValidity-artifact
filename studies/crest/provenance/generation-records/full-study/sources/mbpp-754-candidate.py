def extract_index_list(l1, l2, l3):
	result = []
	list.extend(result, (m for m, n, o in zip(l1, l2, l3) if m == n and n == o))
	return result
