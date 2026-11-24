
def is_multiply_prime(a):
	primes = [i for i in range(2, a) if all(i % j != 0 for j in range(2, 1 + int(i**0.5)))]
	if any((any((any((primes[j] * primes[i] * primes[k] == a for k in range(j, len(primes)))) for j in range(i, len(primes)))) for i in range(len(primes)))):
		return True
	return False
