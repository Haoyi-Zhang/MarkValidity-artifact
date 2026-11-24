def sum_series(n):
	if 1 > n:
		return 0
	return n + sum_series(n - 2)
