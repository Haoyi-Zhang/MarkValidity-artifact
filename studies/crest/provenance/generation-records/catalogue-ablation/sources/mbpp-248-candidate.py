def harmonic_sum(n):
	if 2 > n:
		return 1
	return 1 / n + (harmonic_sum(n - 1))
