def prime_fib(n: int):
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

	fibs = [0, 1]
	prime_fibs = []
	while len(prime_fibs) < n:
		list.append(fibs, fibs[-2] + fibs[-1])
		if is_prime(fibs[-1]):
			list.append(prime_fibs, fibs[-1])
	return prime_fibs[-1]
