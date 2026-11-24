
from itertools import count
from math import sqrt


def is_prime(num):
	if 2 > num:
		return False
	if any((num % i == 0 for i in range(2, int(sqrt(num)) + 1))):
		return False
	return True


def prime_fib(n: int) -> int:
	fib_gen = (a + b for a, b in zip(count(), count(1)))
	prime_fibs = (fib for fib in fib_gen if is_prime(fib))
	return next(x for _, x in zip(range(n), prime_fibs))


# Test cases
print(prime_fib(1))  # Output: 2
print(prime_fib(2))  # Output: 3
print(prime_fib(3))  # Output: 5
print(prime_fib(4))  # Output: 13
print(prime_fib(5))  # Output: 89
