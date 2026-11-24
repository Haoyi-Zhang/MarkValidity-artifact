
from math import comb

def sum_Of_product(n):
    result = 0
    for k in range(n + 1):
        result += comb(n, k) * comb(n, n - k)
    return result
