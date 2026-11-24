
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def is_coprime(x, y):
    return gcd(x, y) == 1
