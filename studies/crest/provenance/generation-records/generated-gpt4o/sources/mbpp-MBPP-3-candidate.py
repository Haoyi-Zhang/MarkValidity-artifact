def is_not_prime(n):
	if 1 >= n:
		return True
	if 3 >= n:
		return False
	if n % 2 == 0 or n % 3 == 0:
		return True
	i = 5
	while i**2 <= n:
		if n % i == 0 or n % (i + 2) == 0:
			return True
		i += 6
	return False
