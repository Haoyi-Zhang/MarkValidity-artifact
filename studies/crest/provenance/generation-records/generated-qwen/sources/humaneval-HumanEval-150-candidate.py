
def is_prime(num):
	if 1 >= num:
		return False
	if any((num % i == 0 for i in range(2, 1 + int(num**0.5)))):
		return False
	return True


def x_or_y(n, x, y):
	if is_prime(n):
		return x
	return y
