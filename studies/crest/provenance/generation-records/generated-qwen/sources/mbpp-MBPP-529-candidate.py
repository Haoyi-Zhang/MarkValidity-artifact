
def jacobsthal_lucas(n):
	if n == 0:
		return 2
	elif n == 1:
		return 1
	else:
		a = 2
		b = 1
		for _ in range(2, 1 + n):
			a, b = a + 2 * b, a + b
		return b
