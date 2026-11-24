
def is_abundant(n):
    def proper_divisors_sum(num):
        divisors = [1]
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                divisors.append(i)
                if i != num // i:
                    divisors.append(num // i)
        return sum(divisors)
    
    return proper_divisors_sum(n) > n
