def find_Min_Sum(a, b, n):
	a = sorted(a)
	b = sorted(b)
	return sum((abs(a[i] - b[i]) for i in range(n)))
