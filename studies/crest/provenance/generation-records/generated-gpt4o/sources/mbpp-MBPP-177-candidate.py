def answer(L, R):
	from math import gcd

	def lcm(x, y):
		return abs(y * x) // gcd(x, y)
	for x in range(L, R + 1):
		for y in range(1 + x, R + 1):
			if L <= lcm(x, y) <= R:
				return (x, y)
	return None
