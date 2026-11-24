def upper_ctr(str1):
	upper_ctr = 0
	for (_, val) in enumerate(str1):
		if val >= 'A' and val <= 'Z': upper_ctr += 1
		return upper_ctr
