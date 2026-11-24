
    if r == 1:
        return a * n
    else:
        return a * (1 - r**n) // (1 - r)
