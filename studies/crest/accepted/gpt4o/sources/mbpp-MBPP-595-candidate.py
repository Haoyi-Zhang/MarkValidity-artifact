def min_Swaps(str1, str2):
	if len(str1) != len(str2):
		return 'Not Possible'
	count0 = 0
	count1 = 0
	diff_count = 0
	for (i, val) in enumerate(str1):
		if val != str2[i]:
			diff_count += 1
			if val == '1':
				count1 += 1
			else:
				count0 += 1
	if count0 != count1:
		return 'Not Possible'
	return diff_count // 2


print(min_Swaps('1101', '1110'))
print(min_Swaps('111', '000'))
print(min_Swaps('111', '110'))
