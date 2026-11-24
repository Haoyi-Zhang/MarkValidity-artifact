
def gcd(a, b):
	while b:
		a, b = b, a % b
	return a


def sum_of_common_divisors(x, y):
	return sum((i for i in range(1, gcd(x, y) + 1) if x % i == 0 and y % i == 0))


def sum1(a, b):
	return sum_of_common_divisors(a, b)
