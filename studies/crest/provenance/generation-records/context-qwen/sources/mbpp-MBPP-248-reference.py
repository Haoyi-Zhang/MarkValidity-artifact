
def harmonic_sum(n):
    if n < 2:
        return 1
    else:
        return 1 / (n - 1) + harmonic_sum(n - 1)
