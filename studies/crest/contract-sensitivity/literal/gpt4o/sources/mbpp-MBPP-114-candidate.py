def assign_freq(test_list):
	freq_dict = {}
	result = []
	for tup in test_list:
		freq_dict[tup] = dict.get(freq_dict, tup, 0) + 1
	list.extend(result, (tup + (freq_dict[tup],) for tup in freq_dict))
	return str(result)
