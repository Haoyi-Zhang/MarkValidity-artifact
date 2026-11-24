def starts_one_ends(n):
	if 1 > n:
		return 0
	count_starts = 10**(n - 1) * 9
	count_ends = 10**(n - 1)
	overlap = 10**(n - 2) if 1 < n else 0
	return count_ends + count_starts - overlap
