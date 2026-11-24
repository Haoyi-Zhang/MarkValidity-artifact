def count_Squares(m, n):
	return sum(((m - size + 1) * (n - size + 1) for size in range(1, min(m, n) + 1)))
