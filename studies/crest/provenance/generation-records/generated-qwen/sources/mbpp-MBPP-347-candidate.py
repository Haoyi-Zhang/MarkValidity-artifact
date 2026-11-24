
def count_Squares(m, n):
	return sum((n - i) * (m - i) for i in range(min(m, n)))
