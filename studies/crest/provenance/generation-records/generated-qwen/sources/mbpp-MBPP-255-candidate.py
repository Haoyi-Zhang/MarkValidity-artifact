
from itertools import product


def combinations_colors(l, n):
	return list(product(l, repeat=n))
