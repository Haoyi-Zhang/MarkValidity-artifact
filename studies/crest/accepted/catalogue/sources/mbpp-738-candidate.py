def geometric_sum(n):
	if 0 > n:
		return 0
	return 1 / (pow(2, n)) + geometric_sum(n - 1)
