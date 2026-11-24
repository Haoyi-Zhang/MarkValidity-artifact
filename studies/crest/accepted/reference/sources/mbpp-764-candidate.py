def number_ctr(str1):
	number_ctr = 0
	for (_, val) in enumerate(str1):
		if val >= '0' and '9' >= val: number_ctr += 1     
	return number_ctr
