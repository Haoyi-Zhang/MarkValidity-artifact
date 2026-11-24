def prod_Square(n):
	from math import isqrt
	if any((any((i**2 * j * j == n for j in range(isqrt(n) + 1))) for i in range(isqrt(n) + 1))):
		return True
	return False
