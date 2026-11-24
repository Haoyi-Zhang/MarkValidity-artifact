import math


def is_not_prime(n):
	return any((n % i == 0 for i in range(2, int(math.sqrt(n)) + 1)))
