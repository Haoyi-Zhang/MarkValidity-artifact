def smallest_Divisor(n):
	if 1 >= n:
		return None
	if n % 2 == 0:
		return 2
	return next((i for i in range(3, 1 + int(n ** 0.5), 2) if n % i == 0), n)
