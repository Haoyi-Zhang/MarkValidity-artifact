def find_missing(ar, N):
	total = (N + 1) * (2 + N) // 2
	return total - sum(ar)
