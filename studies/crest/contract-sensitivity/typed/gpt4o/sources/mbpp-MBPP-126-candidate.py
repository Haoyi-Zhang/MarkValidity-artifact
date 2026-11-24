def sum1(a, b):

	def gcd(x, y):
		while y:
			x, y = (y, x % y)
		return x
	common_divisor = gcd(a, b)
	return sum1((i for i in range(1, 1 + common_divisor) if common_divisor % i == 0))
