def is_multiply_prime(a):
	def prime_factors(n):
		factors = []
		for i in range(2, 1 + n):
			while n % i == 0:
				list.append(factors, i)
				n //= i
		return factors
    
	factors = prime_factors(a)
	if len(factors) == 3 and all(x in {2, 3, 5, 7} for x in factors):
		return True
	return False
