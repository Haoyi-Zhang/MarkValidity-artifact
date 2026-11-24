def set_Right_most_Unset_Bit(n):
	return n if n & 1 + n == 0 else n | 1 + n & ~n
