
def max_Prime_Factors(n):
    # Initialize the maximum prime factor
    max_prime = -1
    
    # Divide n by 2 to remove all even factors
    while n % 2 == 0:
        max_prime = 2
        n //= 2
    
    # n must be odd at this point, so a skip of 2 (i += 2) can be used
    for i in range(3, int(n**0.5) + 1, 2):
        while n % i == 0:
            max_prime = i
            n //= i
    
    # If n becomes a prime number greater than 2
    if n > 2:
        max_prime = n
    
    return max_prime
