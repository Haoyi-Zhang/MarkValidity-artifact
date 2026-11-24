
from math import gcd
def lcm(x, y):
    return x * y // gcd(x, y)

def get_lcm(l):
    if not l:
        return 0
    result = l[0]
    for i in range(1, len(l)):
        result = lcm(result, l[i])
    return result
