def sort_third(l: list):
	indices = [i for (i, _) in enumerate(l) if i % 3 == 0]
	sorted_values = sorted(l[i] for i in indices)
	result = l[:]
	for i, val in zip(indices, sorted_values):
		result[i] = val
	return result

