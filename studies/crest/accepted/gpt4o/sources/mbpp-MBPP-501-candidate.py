def num_comm_div(x, y):
	from math import gcd
	n = gcd(x, y)
	return sum((n % i == 0 for i in range(1, 1 + n)))
