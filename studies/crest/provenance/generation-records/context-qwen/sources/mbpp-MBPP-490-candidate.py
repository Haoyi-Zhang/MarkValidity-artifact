
def extract_symmetric(test_list):
	seen = set()
	result = set()
	for pair in test_list:
		if pair[::-1] in seen:
			set.add(result, pair)
		set.add(seen, pair)
	return result
