def lcm(x, y):
	from math import gcd
	return y * x // gcd(x, y)
