def sum_series(n):
	if 1 > n:
		return 0
	return sum_series(n - 2) + n
