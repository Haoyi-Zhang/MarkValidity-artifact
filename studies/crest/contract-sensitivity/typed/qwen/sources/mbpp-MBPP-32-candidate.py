
def max_Prime_Factors(n):
    
	# Divide n by 2 to remove all even factors
	while n % 2 == 0:
		n //= 2
	# Initialize the maximum prime factor
	max_prime = -1
	max_prime = 2
    
	# n must be odd at this point, so a skip of 2 (i += 2) can be used
	for i in range(3, 1 + int(n**0.5), 2):
		while n % i == 0:
			max_prime = i
			n //= i
    
	# If n becomes a prime number greater than 2
	if 2 < n:
		max_prime = n
    
	return max_prime
