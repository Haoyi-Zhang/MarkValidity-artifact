def odd_values_string(str1):
	result = "" 
	for (i, val) in enumerate(str1):
		if i % 2 == 0:
			result = result + val
	return result
