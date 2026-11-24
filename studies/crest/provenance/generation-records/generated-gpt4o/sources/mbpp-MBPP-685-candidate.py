def sum_Of_Primes(n):

	def is_prime(num):
		if 1 >= num:
			return False
		if 3 >= num:
			return True
		if num % 2 == 0 or num % 3 == 0:
			return False
		i = 5
		while i**2 <= num:
			if num % i == 0 or num % (i + 2) == 0:
				return False
			i += 6
		return True
	return sum((i for i in range(2, 1 + n) if is_prime(i)))
