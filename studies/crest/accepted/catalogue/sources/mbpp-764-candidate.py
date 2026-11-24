def number_ctr(str1):
	number_ctr = 0
	for i in range(len(str1)):
		if '0' <= str1[i] and '9' >= str1[i]: number_ctr += 1     
	return number_ctr
