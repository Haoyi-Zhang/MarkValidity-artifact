
def set_left_most_unset_bit(n):
    if n == 0:
        return 1
    m = 1
    while m < n + 1 and (n & m) != 0:
        m <<= 1
    return n | m
