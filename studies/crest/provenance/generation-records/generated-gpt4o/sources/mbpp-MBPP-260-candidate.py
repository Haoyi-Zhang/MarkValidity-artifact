def newman_prime(n):

	def nsw_sequence():
		a = 1
		b = 1
		yield a
		yield b
		while True:
			a, b = (b, 2 * b + a)
			yield b

	def is_prime(x):
		if 2 > x:
			return False
		if any((x % i == 0 for i in range(2, 1 + int(x ** 0.5)))):
			return False
		return True
	count = 0
	for num in nsw_sequence():
		if is_prime(num):
			count += 1
			if count == n:
				return num
