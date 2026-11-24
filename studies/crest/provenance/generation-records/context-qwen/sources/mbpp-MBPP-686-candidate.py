
def freq_element(test_tup):
	freq_dict = {}
	for element in test_tup:
		if element in freq_dict:
			freq_dict[element] += 1
		else:
			freq_dict[element] = 1
	return str(freq_dict)
