def is_multiply_prime(a):
    def prime_factors(n):
        factors = []
        for i in range(2, n + 1):
            while n % i == 0:
                factors.append(i)
                n //= i
        return factors
    
    factors = prime_factors(a)
    if len(factors) == 3 and all(x in {2, 3, 5, 7} for x in factors):
        return True
    return False