def get_noOfways(n):
	if 2 >= n:
		return n
	a = 1
	b = 2
	for _ in range(3, 1 + n):
		a, b = (b, a + b)
	return b
