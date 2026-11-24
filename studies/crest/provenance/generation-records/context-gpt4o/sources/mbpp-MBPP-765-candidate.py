def is_polite(n):
	count = 0
	num = 1
	while count < n:
		current = num
		factors = sum((current % i == 0 for i in range(1, current + 1)))
		if factors != 2:
			count += 1
		num += 1
	return num - 1
