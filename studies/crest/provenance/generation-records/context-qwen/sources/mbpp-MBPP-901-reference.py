
import math

def lcm(x, y):
    return x * y // math.gcd(x, y)

def smallest_multiple(n):
    result = 1
    for i in range(2, n + 1):
        result = lcm(result, i)
    return result
