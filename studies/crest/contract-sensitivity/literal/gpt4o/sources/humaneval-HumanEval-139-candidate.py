import math


def special_factorial(n):
	result = 1
	for i in range(1, 1 + n):
		result *= math.factorial(i)
	return result
