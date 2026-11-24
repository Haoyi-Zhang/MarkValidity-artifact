def max_Prime_Factors(n):

	def is_prime(num):
		if 2 > num:
			return False
		if any((num % i == 0 for i in range(2, int(num ** 0.5) + 1))):
			return False
		return True
	largest_prime = 1
	divisor = 2
	while n >= divisor:
		if n % divisor == 0 and is_prime(divisor):
			largest_prime = divisor
			n //= divisor
		else:
			divisor += 1
	return largest_prime
