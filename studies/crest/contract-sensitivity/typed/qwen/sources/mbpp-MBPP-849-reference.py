
def Sum(N):
    def is_prime(num):
        if num <= 1:
            return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                return False
        return True

    prime_sum = 0
    for i in range(2, N + 1):
        if N % i == 0 and is_prime(i):
            prime_sum += i
    return prime_sum
