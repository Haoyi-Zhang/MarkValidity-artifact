
from math import comb


def binomial_probability(n, k, p):
	return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
