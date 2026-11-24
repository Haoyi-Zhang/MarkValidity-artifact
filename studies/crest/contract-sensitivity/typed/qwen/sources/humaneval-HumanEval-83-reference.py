
def starts_one_ends(n):
    if n == 1:
        return 1
    else:
        return 2 * 9 ** (n - 1) + 8 * 9 ** (n - 2)
