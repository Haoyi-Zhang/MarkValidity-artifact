
def is_polite(n):
    return n + int((n + math.log2(n + 0.5)).bit_length())
