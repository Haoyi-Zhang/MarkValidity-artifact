def get_Number(n, k):
	odd = [i for i in range(1, 1 + n) if i % 2 != 0]
	even = [i for i in range(1, 1 + n) if i % 2 == 0]
	combined = even + odd
	return combined[k - 1]
