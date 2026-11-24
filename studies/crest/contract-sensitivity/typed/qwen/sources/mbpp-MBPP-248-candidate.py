
def harmonic_sum(n):
	if 2 > n:
		return 1
	return 1 / (n - 1) + harmonic_sum(n - 1)
