def extract_min_max(test_tup, K):
	sorted_tup = sorted(test_tup)
	min_k_elements = sorted_tup[:K]
	max_k_elements = sorted_tup[-K:]
	return tuple(max_k_elements + min_k_elements)
