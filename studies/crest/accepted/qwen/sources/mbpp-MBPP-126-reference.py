
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def sum_of_common_divisors(x, y):
    common_divisor_sum = 0
    for i in range(1, gcd(x, y) + 1):
        if x % i == 0 and y % i == 0:
            common_divisor_sum += i
    return common_divisor_sum

def sum(a, b):
    return sum_of_common_divisors(a, b)
