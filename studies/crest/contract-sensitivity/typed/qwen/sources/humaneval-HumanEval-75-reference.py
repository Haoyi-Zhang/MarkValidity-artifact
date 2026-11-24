
def is_multiply_prime(a):
    primes = [i for i in range(2, a) if all(i % j != 0 for j in range(2, int(i**0.5) + 1))]
    for i in range(len(primes)):
        for j in range(i, len(primes)):
            for k in range(j, len(primes)):
                if primes[i] * primes[j] * primes[k] == a:
                    return True
    return False
