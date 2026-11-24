
def is_not_prime(n):
	if 1 >= n:
		return True
	if n == 2:
		return False
	if any((n % i == 0 for i in range(2, 1 + int(n**0.5)))):
		return True
	return False
