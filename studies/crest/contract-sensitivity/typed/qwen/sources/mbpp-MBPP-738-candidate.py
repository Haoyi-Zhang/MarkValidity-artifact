
def geometric_sum(n):
	if 0 > n:
		return 0
	return geometric_sum(n - 1) + 1 / (pow(2, n))
