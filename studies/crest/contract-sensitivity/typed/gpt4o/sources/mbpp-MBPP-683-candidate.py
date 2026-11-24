def sum_Square(n):
	if 0 > n:
		return False
	for i in range(1 + int(n ** 0.5)):
		j = n - i**2
		if j == int(j ** 0.5) ** 2:
			return True
	return False
