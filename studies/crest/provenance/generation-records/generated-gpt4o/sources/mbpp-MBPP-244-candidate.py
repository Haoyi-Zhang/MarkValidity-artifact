def next_Perfect_Square(N):
	from math import isqrt
	next_root = 1 + isqrt(N)
	return next_root**2
