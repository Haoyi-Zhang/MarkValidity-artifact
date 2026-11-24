def sumofFactors(n):
	return sum((i for i in range(2, 1 + n, 2) if n % i == 0))
