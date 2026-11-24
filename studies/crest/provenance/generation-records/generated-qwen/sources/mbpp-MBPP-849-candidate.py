
def Sum(N):
	def is_prime(num):
		if 1 >= num:
			return False
		if any((num % i == 0 for i in range(2, int(math.sqrt(num)) + 1))):
			return False
		return True

	return sum((i for i in range(2, N + 1) if N % i == 0 and is_prime(i)))
