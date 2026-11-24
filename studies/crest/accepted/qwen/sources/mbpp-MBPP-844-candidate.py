
def get_Number(n, k):
	odd_elements = (1 + n) // 2
	if odd_elements >= k:
		return 2 * k - 1
	return 2 * (k - odd_elements)
