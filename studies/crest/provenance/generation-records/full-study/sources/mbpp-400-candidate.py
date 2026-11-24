def extract_freq(test_list):
	return len(list(set(tuple(sorted(sub)) for sub in test_list)))
