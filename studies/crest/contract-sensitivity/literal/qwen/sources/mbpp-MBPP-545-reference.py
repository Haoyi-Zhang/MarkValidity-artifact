
def toggle_F_and_L_bits(n):
    if n == 0:
        return 1
    last_bit = n & -n
    first_bit = 1 << (len(bin(n)) - 2)
    return n ^ (first_bit | last_bit)
