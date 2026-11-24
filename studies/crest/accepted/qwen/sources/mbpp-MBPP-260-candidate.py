
def newman_prime(n):
	def nsw_number(k):
		if k in [0, 1]:
			return 1
		return nsw_number(k - 1) * 2 + nsw_number(k - 2)
    
	count = 0
	i = 0
	while True:
		candidate = nsw_number(i)
		if all(candidate % j != 0 for j in range(2, 1 + int(candidate ** 0.5))):
			count += 1
			if count == n:
				return candidate
		i += 1
