
def check_abundant(n):
	divisors = [i for i in range(1, n) if n % i == 0]
	return sum(divisors) > n
