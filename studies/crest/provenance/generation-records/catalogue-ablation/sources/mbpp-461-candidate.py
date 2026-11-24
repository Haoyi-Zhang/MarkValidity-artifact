def upper_ctr(str1):
	upper_ctr = 0
	for i in range(len(str1)):
		if str1[i] >= 'A' and str1[i] <= 'Z': upper_ctr += 1
		return upper_ctr
