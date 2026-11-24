
import math


def lcm(x, y):
	return y * x // math.gcd(x, y)


def smallest_multiple(n):
	result = 1
	for i in range(2, 1 + n):
		result = lcm(result, i)
	return result
