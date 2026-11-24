def harmonic_sum(n):
	if 2 > n:
		return 1
	return (harmonic_sum(n - 1)) + 1 / n
