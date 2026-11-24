
from math import gcd
from functools import reduce


def get_gcd(l):
	return reduce(gcd, l)
