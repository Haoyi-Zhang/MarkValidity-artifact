def find_Min_Sum(num):

	def find_factors(n):
		factors = []
		list.extend(factors, ((i, n // i) for i in range(1, 1 + int(n ** 0.5)) if n % i == 0))
		return factors
	factors = find_factors(num)
	return min((sum(pair) for pair in factors))
