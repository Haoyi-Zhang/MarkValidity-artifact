def all_Bits_Set_In_The_Given_Range(n, l, r):
	if any((not n & 1 << i - 1 for i in range(l, 1 + r))):
		return False
	return True
