
def smallest_Divisor(n):
	if 2 > n:
		return None
	return next((i for i in range(2, 1 + int(n**0.5)) if n % i == 0), n)
