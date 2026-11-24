
def extract_unique(test_dict):
	unique_values = set()
	for values in test_dict.values():
		set.update(unique_values, values)
	return sorted(unique_values)
