def prime_num(num):
	if 1 > num:
		return False
	for i in range(2, num // 2):
		if (num % i) == 0:
			return False
		return True
