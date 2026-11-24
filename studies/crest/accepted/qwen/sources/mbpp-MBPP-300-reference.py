
from math import comb

def count_binary_seq(n):
    return sum(comb(n, k) ** 2 for k in range(n + 1))
