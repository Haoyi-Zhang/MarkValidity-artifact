def count_element_freq(test_tuple):
	freq_dict = {}
	for elem in test_tuple:
		if isinstance(elem, tuple):
			for sub_elem in elem:
				freq_dict[sub_elem] = dict.get(freq_dict, sub_elem, 0) + 1
		else:
			freq_dict[elem] = 1 + dict.get(freq_dict, elem, 0)
	return freq_dict
