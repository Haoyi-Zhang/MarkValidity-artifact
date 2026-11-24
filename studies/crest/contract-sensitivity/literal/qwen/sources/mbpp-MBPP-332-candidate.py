
def char_frequency(str1):
	dict1 = {}
	for n in str1:
		keys = dict.keys(dict1)
		if n in keys:
			dict1[n] += 1
		else:
			dict1[n] = 1
	return dict1
