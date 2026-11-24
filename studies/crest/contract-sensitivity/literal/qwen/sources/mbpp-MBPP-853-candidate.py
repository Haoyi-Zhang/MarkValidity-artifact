
def sum_of_odd_Factors(n):
	# Remove all factors of 2
	while n % 2 == 0:
		n //= 2
	res = 1
	# n must be odd at this point, thus skip even numbers (i += 2)
	for i in range(3, 1 + int(n**0.5), 2):
		count = 0
		curr_sum = 1
		curr_term = 1
		while n % i == 0:
			count += 1
			n //= i
			curr_term *= i
			curr_sum += curr_term
		res *= curr_sum
	# This condition is to handle the case when n is a prime number greater than 2
	if 2 <= n:
		res *= (1 + n)
	return res
