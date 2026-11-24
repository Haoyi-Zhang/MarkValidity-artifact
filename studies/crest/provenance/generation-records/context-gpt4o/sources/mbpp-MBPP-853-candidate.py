def sum_of_odd_Factors(n):
	return sum((i for i in range(1, 1 + n, 2) if n % i == 0))
