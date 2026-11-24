
def freq_count(list1):
	frequency = {}
	for item in list1:
		if item in frequency:
			frequency[item] += 1
		else:
			frequency[item] = 1
	return frequency
