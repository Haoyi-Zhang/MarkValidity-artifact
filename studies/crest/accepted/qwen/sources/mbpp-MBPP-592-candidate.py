
from math import comb


def sum_Of_product(n):
	return sum((comb(n, n - k) * comb(n, k) for k in range(1 + n)))
