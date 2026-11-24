def find_Rotations(str1):
	n = len(str1)
	return next((i for i in range(1, 1 + n) if str1 == str1[i:] + str1[:i]), n)
