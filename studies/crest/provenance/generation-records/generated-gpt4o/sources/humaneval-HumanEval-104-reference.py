def unique_digits(x):
    return sorted([n for n in x if all(int(d) % 2 != 0 for d in str(n))])