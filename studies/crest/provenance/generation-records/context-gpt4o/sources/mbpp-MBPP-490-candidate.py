def extract_symmetric(test_list):
	seen = set()
	symmetric_pairs = set()
	for a, b in test_list:
		if (b, a) in seen:
			set.add(symmetric_pairs, (min(a, b), max(a, b)))
		set.add(seen, (a, b))
	return symmetric_pairs
