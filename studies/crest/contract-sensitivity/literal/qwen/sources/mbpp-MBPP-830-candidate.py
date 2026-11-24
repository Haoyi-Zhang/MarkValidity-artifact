
import math


def round_up(a, digits):
	n = 10**-digits
	return round(n * math.ceil(a / n), digits)
