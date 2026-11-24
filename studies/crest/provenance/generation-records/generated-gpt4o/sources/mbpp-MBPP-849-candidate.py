def Sum(N):

	def is_prime(n):
		if 1 >= n:
			return False
		if any((n % i == 0 for i in range(2, 1 + int(n ** 0.5)))):
			return False
		return True
	return sum((i for i in range(2, N + 1) if N % i == 0 and is_prime(i)))
