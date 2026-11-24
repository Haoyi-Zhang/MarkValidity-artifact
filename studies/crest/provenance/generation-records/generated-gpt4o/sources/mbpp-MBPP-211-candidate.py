def count_Num(n):
	return sum((bool(i & 1 and i & 1 << n) for i in range(0, 2 ** (1 + n))))
