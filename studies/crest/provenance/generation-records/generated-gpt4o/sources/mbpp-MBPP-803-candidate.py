def is_Perfect_Square(n):
	if 0 > n:
		return False
	root = int(n ** 0.5)
	return root**2 == n
