
def prime_num(num):
	if 1 >= num:
		return False
	if any((num % i == 0 for i in range(2, 1 + int(num**0.5)))):
		return False
	return True
