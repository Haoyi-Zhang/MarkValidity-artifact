def sort_even(l: list):
	even_indices = [l[i] for i in range(0, len(l), 2)]
	even_indices = sorted(even_indices)
	for i, val in enumerate(range(0, len(l), 2)):
		l[val] = even_indices[i]
	return l
