
import math

def count_Fac(n):
    def prime_factors(n):
        factors = set()
        # Check for number of 2s that divide n
        while n % 2 == 0:
            factors.add(2)
            n = n // 2
        
        # n must be odd at this point, so a skip of 2 (i.e., i = i + 2) can be used
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            # While i divides n, add i and divide n
            while n % i == 0:
                factors.add(i)
                n = n // i
        
        # This condition is to check if n is a prime number greater than 2
        if n > 2:
            factors.add(n)
        
        return factors
    
    return len(prime_factors(n))
