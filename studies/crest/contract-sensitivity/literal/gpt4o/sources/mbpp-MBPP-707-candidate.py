def count_Set_Bits(n):
	count = 0
	for i in range(1, 1 + n):
		count += bin(i).count('1')
	return count
