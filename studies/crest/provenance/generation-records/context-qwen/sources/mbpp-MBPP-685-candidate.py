
def sum_Of_Primes(n):
	def is_prime(num):
		if 2 > num:
			return False
		if any((num % i == 0 for i in range(2, 1 + int(num**0.5)))):
			return False
		return True

	return sum((i for i in range(2, 1 + n) if is_prime(i)))
