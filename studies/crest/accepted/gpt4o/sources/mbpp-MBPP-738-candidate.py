def geometric_sum(n):
	if n == 0:
		return 0
	return geometric_sum(n - 1) + 1 / 2 ** (n - 1)
