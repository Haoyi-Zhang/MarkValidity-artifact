
def count_With_Odd_SetBits(n):
	return sum(bin(i).count('1') % 2 for i in range(1, 1 + n))
