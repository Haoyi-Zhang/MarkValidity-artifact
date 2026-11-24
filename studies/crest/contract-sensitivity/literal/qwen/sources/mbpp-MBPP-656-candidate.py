
def find_Min_Sum(a, b, n):
	a = sorted(a)
	b = sorted(b)
	return sum(abs(x - y) for x, y in zip(a, b))
