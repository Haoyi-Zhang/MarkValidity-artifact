
    if n < 2:
        return n
    length = len(bin(n)) - 3
    mask = (1 << (length - 1)) - 1
    mask <<= 1
    mask += 1
    return n ^ mask
