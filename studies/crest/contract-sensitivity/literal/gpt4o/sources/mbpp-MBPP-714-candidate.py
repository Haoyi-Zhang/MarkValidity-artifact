def count_Fac(n):
	count = 0
	i = 2
	while i**2 <= n:
		if n % i == 0:
			count += 1
			while n % i == 0:
				n //= i
		i += 1
	if 1 < n:
		count += 1
	return count
