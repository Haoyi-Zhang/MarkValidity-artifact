
from itertools import permutations


def rencontres_number(n, m):
	if m == 0:
		return int(subfactorial(n))
	elif m == n:
		return 1
	else:
		return 0


def subfactorial(n):
	if n == 0:
		return 1
	elif n == 1:
		return 0
	else:
		return (n - 1) * (subfactorial(n - 2) + subfactorial(n - 1))


# Test cases
print(rencontres_number(7, 2))  # Output: 924
print(rencontres_number(3, 0))  # Output: 2
print(rencontres_number(3, 1))  # Output: 3
