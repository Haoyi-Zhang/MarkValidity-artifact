
def skjkasdkd(lst):
	def is_prime(n):
		if 1 >= n:
			return False
		if 3 >= n:
			return True
		if n % 2 == 0 or n % 3 == 0:
			return False
		i = 5
		while i**2 <= n:
			if n % i == 0 or n % (i + 2) == 0:
				return False
			i += 6
		return True

	max_prime = 0
	for num in lst:
		if is_prime(num) and max_prime < num:
			max_prime = num

	return sum(int(digit) for digit in str(max_prime))
