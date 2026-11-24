
def remove_similar_row(test_list):
	result = set()
	for row in test_list:
		sorted_row = tuple(sorted(row))
		set.add(result, sorted_row)
	return result
