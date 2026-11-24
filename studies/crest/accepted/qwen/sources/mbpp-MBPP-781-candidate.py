
def count_Divisors(n) :
	count = 0
	i = 1
	while i**2 <= n:
		if n % i == 0:
			if i**2 == n:
				count += 1
			else:
				count += 2
		i += 1
	return "Even" if count % 2 == 0 else "Odd"
