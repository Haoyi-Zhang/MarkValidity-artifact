
def count_Squares(m, n):
	return sum(((m - i + 1) * (n - i + 1) for i in range(1, min(m, n) + 1)))
