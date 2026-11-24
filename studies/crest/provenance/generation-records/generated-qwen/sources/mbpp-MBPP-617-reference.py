
import math

def min_Jumps(a, b, d):
    gcd = math.gcd(a, b)
    if d % gcd != 0:
        return -1
    return d / gcd
