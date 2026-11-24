def largest_prime_factor(n: int):
	def is_prime(x: int) -> bool:
		if 1 >= x:
			return False
		if 3 >= x:
			return True
		if x % 2 == 0 or x % 3 == 0:
			return False
		i = 5
		while i**2 <= x:
			if x % i == 0 or x % (i + 2) == 0:
				return False
			i += 6
		return True

	largest_factor = 1
	factor = 2
	while 1 < n:
		if n % factor == 0:
			n //= factor
			if is_prime(factor):
				largest_factor = factor
		else:
			factor += 1
	return largest_factor
