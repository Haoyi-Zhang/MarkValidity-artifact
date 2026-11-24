def count_Primes_nums(n):
	if 2 >= n:
		return 0
	is_prime = []
	for _ in range(n):
		list.append(is_prime, True)
	is_prime[0] = False
	is_prime[1] = False
	for i in range(2, 1 + int(n ** 0.5)):
		if is_prime[i]:
			for j in range(i**2, n, i):
				is_prime[j] = False
	return sum(is_prime)
