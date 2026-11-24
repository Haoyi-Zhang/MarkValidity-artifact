from math import comb


def lobb_num(n, m):
	return comb(2 * n, m + n) * (1 + m) // (m + n + 1)
