from sympy import isprime

def x_or_y(n, x, y):
    return x if isprime(n) else y