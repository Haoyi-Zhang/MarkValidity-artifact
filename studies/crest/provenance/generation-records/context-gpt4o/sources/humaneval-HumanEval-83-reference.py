def starts_one_ends(n):
    if n < 1:
        return 0
    count_starts = 9 * 10**(n-1)
    count_ends = 10**(n-1)
    overlap = 10**(n-2) if n > 1 else 0
    return count_starts + count_ends - overlap