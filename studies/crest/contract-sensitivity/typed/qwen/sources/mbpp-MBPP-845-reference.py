
import math

def find_Digits(n):
    if n < 0:
        return 0
    elif n <= 1:
        return 1
    
    x = (n * math.log10(n / math.e) + math.log10(2 * math.pi * n) / 2.0)
    
    return int(x) + 1
