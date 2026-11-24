def find_Rotations(str1): 
	tmp = str1 + str1
	n = len(str1) 
	for i in range(1, 1 + n): 
		substring = tmp[i: i + n] 
		if (str1 == substring): 
			return i 
	return n
