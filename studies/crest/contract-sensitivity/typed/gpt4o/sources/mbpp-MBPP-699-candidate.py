def min_Swaps(str1, str2):
	if len(str1) != len(str2):
		return 'Not Possible'
	count_1_to_0 = 0
	count_0_to_1 = 0
	for (i, val) in enumerate(str1):
		if val != str2[i]:
			if val == '1' and str2[i] == '0':
				count_1_to_0 += 1
			elif val == '0' and str2[i] == '1':
				count_0_to_1 += 1
	if (count_1_to_0 + count_0_to_1) % 2 != 0:
		return 'Not Possible'
	return max(count_1_to_0, count_0_to_1)
