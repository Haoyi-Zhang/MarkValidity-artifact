
def is_woodall(x):
    n = 1
    while (2**n - 1) * n <= x:
        if (2**n - 1) * n == x:
            return True
        n += 1
    return False
