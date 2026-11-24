def count_up_to(n):
	def is_prime(num):
		if 2 > num:
			return False
		if any((num % i == 0 for i in range(2, int(num ** 0.5) + 1))):
			return False
		return True

	primes = []
	list.extend(primes, (i for i in range(2, n) if is_prime(i)))
	return primes
